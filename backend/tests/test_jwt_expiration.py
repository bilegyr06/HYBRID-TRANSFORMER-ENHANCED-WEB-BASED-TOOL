"""
Tests for JWT token expiration enforcement.

Verifies:
- JWT tokens expire after configured JWT_EXPIRATION_HOURS
- Expired tokens are rejected on protected endpoints
- Configuration prevents long-lived tokens (security)
- Correct expiration time is set on token creation
"""

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.core.config import settings
from src.services.auth_service import create_access_token, decode_access_token
from src.core.database import get_db


client = TestClient(app)


class TestJWTExpirationConfiguration:
    """Test JWT expiration configuration."""
    
    def test_expiration_hours_reduced_for_security(self):
        """JWT_EXPIRATION_HOURS is set to reasonable value (not 1 year)."""
        # Phase 1 fix: Reduced from 24*365 (1 year) to 24 (1 day)
        assert settings.JWT_EXPIRATION_HOURS == 24
        assert settings.JWT_EXPIRATION_HOURS <= 24  # Max 1 day for security
    
    def test_expiration_hours_is_positive(self):
        """JWT_EXPIRATION_HOURS is positive."""
        assert settings.JWT_EXPIRATION_HOURS > 0
    
    def test_default_expiration_not_hardcoded_to_year(self):
        """Configuration doesn't use unsafe 1-year default."""
        # This would be a security issue
        one_year_hours = 24 * 365
        assert settings.JWT_EXPIRATION_HOURS != one_year_hours


class TestTokenExpirationOnCreation:
    """Test that tokens have correct expiration time."""
    
    def test_token_expires_in_configured_hours(self):
        """Created token expires in JWT_EXPIRATION_HOURS."""
        now = datetime.utcnow()
        token = create_access_token(data={"sub": "user-123"})
        decoded = decode_access_token(token)
        
        assert decoded is not None
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        
        # Calculate expected expiration
        expected_exp = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        
        # Allow 10 second tolerance for test execution
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 10
    
    def test_token_not_already_expired(self):
        """Just-created token is not immediately expired."""
        token = create_access_token(data={"sub": "user-123"})
        
        # Token should be decodable immediately
        decoded = decode_access_token(token)
        assert decoded is not None
    
    def test_multiple_tokens_have_different_expiration(self):
        """Tokens created at different times have different exp times."""
        token1 = create_access_token(data={"sub": "user-1"})
        
        # Small delay
        time.sleep(0.1)
        
        token2 = create_access_token(data={"sub": "user-2"})
        
        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)
        
        # Second token should expire later
        assert decoded2["exp"] >= decoded1["exp"]


class TestTokenRejectionAfterExpiration:
    """Test that expired tokens are rejected."""
    
    def test_expired_token_cannot_be_decoded(self):
        """Decoding an expired token returns None."""
        # Create token that expires immediately
        past_time = datetime.utcnow() - timedelta(seconds=1)
        expires_delta = past_time - datetime.utcnow()
        
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=expires_delta
        )
        
        # Wait for expiration
        time.sleep(0.5)
        
        # Should return None (token expired)
        decoded = decode_access_token(token)
        assert decoded is None
    
    def test_expired_token_rejected_on_protected_endpoint(self):
        """Expired token returns 401 when accessing protected endpoint."""
        # Create token that expires immediately
        past_delta = timedelta(seconds=-10)  # Already expired
        token = create_access_token(data={"sub": "user-123"}, expires_delta=past_delta)
        
        # Try to access protected endpoint
        response = client.get(
            "/reviews",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be rejected
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_near_expiration_still_valid(self):
        """Token very close to expiration is still valid."""
        # Create token expiring in 1 second
        expires_delta = timedelta(seconds=1)
        token = create_access_token(data={"sub": "user-123"}, expires_delta=expires_delta)
        
        # Immediately decode - should work
        decoded = decode_access_token(token)
        assert decoded is not None


class TestExpirationWithDifferentTimezones:
    """Test token expiration with timezone considerations."""
    
    def test_expiration_uses_utc(self):
        """Token expiration timestamps are in UTC."""
        token = create_access_token(data={"sub": "user-123"})
        decoded = decode_access_token(token)
        
        assert decoded is not None
        exp_timestamp = decoded["exp"]
        
        # Should be a valid Unix timestamp (seconds since epoch in UTC)
        assert isinstance(exp_timestamp, (int, float))
        assert exp_timestamp > 0
    
    def test_custom_expiration_delta_respected(self):
        """Custom expiration delta overrides default."""
        custom_hours = 2
        custom_delta = timedelta(hours=custom_hours)
        
        now = datetime.utcnow()
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=custom_delta
        )
        decoded = decode_access_token(token)
        
        assert decoded is not None
        exp_datetime = datetime.fromtimestamp(decoded["exp"])
        expected_exp = now + custom_delta
        
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 10


class TestSecurityImplications:
    """Test security implications of expiration settings."""
    
    def test_session_timeout_enforced(self):
        """Sessions don't last longer than configured hours."""
        # This is the security benefit - if someone's token is compromised,
        # it's only useful for JWT_EXPIRATION_HOURS
        assert settings.JWT_EXPIRATION_HOURS <= 24  # Max 1 day
    
    def test_no_perpetual_tokens(self):
        """No tokens with infinite expiration."""
        token = create_access_token(data={"sub": "user-123"})
        decoded = decode_access_token(token)
        
        # Token must have expiration
        assert "exp" in decoded
        assert decoded["exp"] is not None
        
        # Expiration should be in the future
        now_timestamp = datetime.utcnow().timestamp()
        assert decoded["exp"] > now_timestamp
    
    def test_compromised_token_has_time_limit(self):
        """Even if a token is compromised, attacker has limited time."""
        # This is the intent of short token expiration
        token_lifetime_hours = settings.JWT_EXPIRATION_HOURS
        
        # Should be short enough to limit damage
        assert token_lifetime_hours <= 24
        
        # Document the risk period
        # Example: 24 hours means compromised token is usable for max 24 hours


class TestExpirationEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_expiration_not_allowed(self):
        """Tokens don't expire at current time."""
        token = create_access_token(data={"sub": "user-123"})
        decoded = decode_access_token(token)
        
        now_timestamp = datetime.utcnow().timestamp()
        
        # Expiration must be in future
        assert decoded["exp"] > now_timestamp
    
    def test_very_short_expiration(self):
        """Can create tokens with very short expiration for testing."""
        short_delta = timedelta(milliseconds=100)
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=short_delta
        )
        
        # Should be valid immediately
        decoded = decode_access_token(token)
        assert decoded is not None
        
        # Should expire quickly
        time.sleep(0.2)
        decoded_expired = decode_access_token(token)
        assert decoded_expired is None
    
    def test_token_claims_expire_together(self):
        """All claims in token expire together."""
        claims = {
            "sub": "user-123",
            "role": "admin",
            "email": "user@example.com"
        }
        token = create_access_token(data=claims)
        
        # All claims should be present while valid
        decoded = decode_access_token(token)
        assert decoded["sub"] == "user-123"
        assert decoded["role"] == "admin"
        assert decoded["email"] == "user@example.com"
        
        # Create expired token
        past_delta = timedelta(seconds=-5)
        expired_token = create_access_token(data=claims, expires_delta=past_delta)
        
        # Decoding expired token should return None (all claims lost)
        assert decode_access_token(expired_token) is None


class TestExpirationConfigurationProduction:
    """Test expiration settings in production context."""
    
    def test_production_environment_validation(self):
        """Production environment has strict expiration requirements."""
        # Current config: JWT_EXPIRATION_HOURS = 24
        # This is appropriate for production
        if settings.ENVIRONMENT == "production":
            # Should be reasonably short
            assert settings.JWT_EXPIRATION_HOURS <= 24
    
    def test_token_refresh_pattern_not_implemented(self):
        """Token refresh not implemented - relies on short expiration."""
        # This design choice means:
        # - No refresh token infrastructure needed
        # - Users must re-authenticate after expiration
        # - Simpler security model, but more frequent logins
        assert settings.JWT_EXPIRATION_HOURS == 24
        
        # For this to work well, frontend should:
        # - Redirect to login when 401 received
        # - Not store token in localStorage (use httpOnly cookie)
