"""
Unit tests for authentication service functions.

Covers:
- Password validation (strength requirements)
- Password hashing with Argon2
- Password verification
- JWT token creation and validation
- Token expiration handling
"""

import pytest
from datetime import datetime, timedelta
from jose import JWTError
from src.services.auth_service import (
    validate_password_strength,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from src.core.config import settings


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_password_too_short(self):
        """Password with < 8 characters rejected."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password_strength("Short1!")
    
    def test_password_missing_uppercase(self):
        """Password without uppercase letter rejected."""
        with pytest.raises(ValueError, match="uppercase"):
            validate_password_strength("lowercase1!")
    
    def test_password_missing_lowercase(self):
        """Password without lowercase letter rejected."""
        with pytest.raises(ValueError, match="lowercase"):
            validate_password_strength("UPPERCASE1!")
    
    def test_password_missing_digit(self):
        """Password without digit rejected."""
        with pytest.raises(ValueError, match="digit"):
            validate_password_strength("NoDigit!Str")
    
    def test_valid_password(self):
        """Valid password passes all checks."""
        # Should not raise
        validate_password_strength("ValidPass123!")
        validate_password_strength("ComplexP@ssw0rd")
        validate_password_strength("Secure1Password")
    
    def test_password_with_special_chars(self):
        """Valid password includes special characters."""
        validate_password_strength("P@ssw0rd#Spec!")


class TestPasswordHashing:
    """Test password hashing with Argon2."""
    
    def test_hash_password_returns_string(self):
        """hash_password returns a string."""
        result = hash_password("ValidPass123!")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_hash_password_validates_strength(self):
        """hash_password validates password before hashing."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            hash_password("short1!")
    
    def test_hashes_are_different_for_same_password(self):
        """Same password produces different hashes (Argon2 uses salt)."""
        password = "ValidPass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
    
    def test_hash_contains_argon2_prefix(self):
        """Argon2 hashes contain '$argon2' prefix."""
        hashed = hash_password("ValidPass123!")
        assert "$argon2" in hashed
    
    def test_hash_length_reasonable(self):
        """Argon2 hash has reasonable length."""
        hashed = hash_password("ValidPass123!")
        # Argon2 hashes are typically 60-100 characters
        assert 50 < len(hashed) < 150


class TestPasswordVerification:
    """Test password verification against hashes."""
    
    def test_verify_correct_password(self):
        """verify_password returns True for correct password."""
        password = "ValidPass123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """verify_password returns False for incorrect password."""
        password = "ValidPass123!"
        wrong_password = "WrongPass123!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_case_sensitive(self):
        """Password verification is case-sensitive."""
        password = "ValidPass123!"
        hashed = hash_password(password)
        
        assert verify_password("validpass123!", hashed) is False
    
    def test_verify_empty_password(self):
        """Verification with empty password fails gracefully."""
        hashed = hash_password("ValidPass123!")
        assert verify_password("", hashed) is False
    
    def test_verify_with_wrong_hash_format(self):
        """Verification fails with invalid hash format."""
        with pytest.raises(Exception):  # Should raise, not crash silently
            verify_password("ValidPass123!", "not-a-valid-hash")


class TestJWTTokenCreation:
    """Test JWT token creation."""
    
    def test_create_access_token_returns_string(self):
        """create_access_token returns a JWT string."""
        token = create_access_token(data={"sub": "123"})
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts: header.payload.signature
    
    def test_token_includes_subject(self):
        """JWT token includes the subject claim."""
        user_id = "user-456"
        token = create_access_token(data={"sub": user_id})
        
        # Decode to verify
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == user_id
    
    def test_token_includes_expiration(self):
        """JWT token includes expiration timestamp."""
        token = create_access_token(data={"sub": "123"})
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert "exp" in decoded
        # exp should be a number (Unix timestamp)
        assert isinstance(decoded["exp"], (int, float))
    
    def test_token_expiration_uses_config_default(self):
        """Token uses JWT_EXPIRATION_HOURS from config."""
        token = create_access_token(data={"sub": "123"})
        decoded = decode_access_token(token)
        
        assert decoded is not None
        exp_timestamp = decoded["exp"]
        now = datetime.utcnow()
        
        # Token expiration should be approximately config.JWT_EXPIRATION_HOURS in future
        expected_exp = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        actual_exp = datetime.fromtimestamp(exp_timestamp)
        
        # Allow 10-second tolerance for test execution time
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 10
    
    def test_token_with_custom_expiration_delta(self):
        """Token respects custom expires_delta parameter."""
        custom_delta = timedelta(hours=2)
        token = create_access_token(data={"sub": "123"}, expires_delta=custom_delta)
        decoded = decode_access_token(token)
        
        assert decoded is not None
        exp_timestamp = decoded["exp"]
        now = datetime.utcnow()
        expected_exp = now + custom_delta
        actual_exp = datetime.fromtimestamp(exp_timestamp)
        
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 10  # 10-second tolerance
    
    def test_token_with_additional_claims(self):
        """Token can include additional claims."""
        claims = {"sub": "user-789", "role": "admin", "email": "admin@example.com"}
        token = create_access_token(data=claims)
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "user-789"
        assert decoded["role"] == "admin"
        assert decoded["email"] == "admin@example.com"


class TestJWTTokenDecoding:
    """Test JWT token validation and decoding."""
    
    def test_decode_valid_token(self):
        """decode_access_token returns claims for valid token."""
        token = create_access_token(data={"sub": "user-100"})
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert isinstance(decoded, dict)
        assert decoded["sub"] == "user-100"
    
    def test_decode_invalid_token_format(self):
        """decode_access_token returns None for malformed token."""
        result = decode_access_token("not.a.valid.token")
        assert result is None
    
    def test_decode_empty_token(self):
        """decode_access_token returns None for empty token."""
        result = decode_access_token("")
        assert result is None
    
    def test_decode_token_with_wrong_secret(self):
        """Token signed with different secret cannot be decoded."""
        # Create token
        token = create_access_token(data={"sub": "user-123"})
        
        # Temporarily change the secret (simulate)
        original_secret = settings.JWT_SECRET_KEY
        settings.JWT_SECRET_KEY = "different-secret-key-not-matching"
        
        try:
            # Decoding with wrong secret should fail
            result = decode_access_token(token)
            assert result is None
        finally:
            # Restore original secret
            settings.JWT_SECRET_KEY = original_secret
    
    def test_decode_expired_token(self):
        """decode_access_token returns None for expired token."""
        # Create token that expires immediately
        past_time = datetime.utcnow() - timedelta(seconds=1)
        past_delta = past_time - datetime.utcnow()
        
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=past_delta
        )
        
        # Wait a moment to ensure expiration
        import time
        time.sleep(0.1)
        
        result = decode_access_token(token)
        assert result is None


class TestAuthServiceIntegration:
    """Integration tests for auth service flow."""
    
    def test_full_registration_flow(self):
        """Test complete password -> hash -> verify flow."""
        password = "SecurePass123!"
        
        # Validate
        validate_password_strength(password)
        
        # Hash
        hashed = hash_password(password)
        
        # Verify
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPass123!", hashed) is False
    
    def test_full_auth_flow(self):
        """Test complete login -> token -> validation flow."""
        user_id = "user-555"
        
        # Create token on login
        token = create_access_token(data={"sub": user_id})
        
        # Validate token
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == user_id
    
    def test_multiple_users_separate_tokens(self):
        """Multiple users get separate tokens."""
        user1_token = create_access_token(data={"sub": "user-1"})
        user2_token = create_access_token(data={"sub": "user-2"})
        
        # Tokens should be different
        assert user1_token != user2_token
        
        # Each decodes to correct user
        decoded1 = decode_access_token(user1_token)
        decoded2 = decode_access_token(user2_token)
        
        assert decoded1["sub"] == "user-1"
        assert decoded2["sub"] == "user-2"
