"""
Tests for user profile endpoints (Phase 3.1).
Testing feature: User profile management.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from src.main import app
from src.core.database import Base, get_db
from src.models.user import User
from src.services.auth_service import hash_password, create_access_token


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user."""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=hash_password("TestPassword123"),
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def test_token(test_user):
    """Create JWT token for test user."""
    return create_access_token(data={"sub": str(test_user.id)})


class TestGetProfile:
    """Tests for GET /api/profile endpoint."""
    
    def test_get_profile_success(self, test_user, test_token):
        """Test successful profile retrieval."""
        response = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] is True
    
    def test_get_profile_missing_auth(self):
        """Test profile retrieval without auth header."""
        response = client.get("/api/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_invalid_token(self):
        """Test profile retrieval with invalid token."""
        response = client.get(
            "/api/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_wrong_auth_scheme(self, test_token):
        """Test profile retrieval with wrong auth scheme."""
        response = client.get(
            "/api/profile",
            headers={"Authorization": f"Basic {test_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_nonexistent_user(self):
        """Test profile retrieval for non-existent user."""
        # Create a token with non-existent user ID
        invalid_token = create_access_token(data={"sub": "99999"})
        response = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateProfile:
    """Tests for PUT /api/profile endpoint."""
    
    def test_update_profile_success(self, test_user, test_token):
        """Test successful profile update."""
        update_data = {
            "full_name": "Updated Name",
            "bio": "This is my bio",
            "organization": "Test Organization",
            "avatar_url": "https://example.com/avatar.jpg"
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["bio"] == "This is my bio"
        assert data["organization"] == "Test Organization"
        assert data["avatar_url"] == "https://example.com/avatar.jpg"
        assert data["profile_updated_at"] is not None
    
    def test_update_profile_partial(self, test_user, test_token):
        """Test partial profile update."""
        update_data = {
            "full_name": "New Name"
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "New Name"
        # Other fields should remain unchanged
        assert data["email"] == test_user.email
    
    def test_update_profile_empty_request(self, test_user, test_token):
        """Test profile update with empty request body."""
        response = client.put(
            "/api/profile",
            json={},
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        # Should return unchanged profile
        data = response.json()
        assert data["id"] == test_user.id
    
    def test_update_profile_bio_too_long(self, test_user, test_token):
        """Test profile update with bio exceeding max length."""
        update_data = {
            "bio": "x" * 501  # Exceeds 500 char limit
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_profile_full_name_too_long(self, test_user, test_token):
        """Test profile update with full_name exceeding max length."""
        update_data = {
            "full_name": "x" * 256  # Exceeds 255 char limit
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_profile_invalid_avatar_url(self, test_user, test_token):
        """Test profile update with invalid avatar URL."""
        update_data = {
            "avatar_url": "invalid-url"  # Should start with http:// or https://
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_profile_valid_avatar_urls(self, test_user, test_token):
        """Test profile update with various valid avatar URLs."""
        valid_urls = [
            "https://example.com/avatar.jpg",
            "http://example.com/avatar.png",
            "https://cdn.example.com/users/avatar.gif"
        ]
        for url in valid_urls:
            response = client.put(
                "/api/profile",
                json={"avatar_url": url},
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["avatar_url"] == url
    
    def test_update_profile_missing_auth(self):
        """Test profile update without auth header."""
        response = client.put(
            "/api/profile",
            json={"full_name": "New Name"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile_invalid_token(self):
        """Test profile update with invalid token."""
        response = client.put(
            "/api/profile",
            json={"full_name": "New Name"},
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProfileStats:
    """Tests for GET /api/profile/stats endpoint."""
    
    def test_get_profile_stats_success(self, test_user, test_token):
        """Test successful stats retrieval."""
        response = client.get(
            "/api/profile/stats",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_reviews" in data
        assert "last_review_date" in data
        assert "account_age_days" in data
        assert "member_since" in data
        assert data["total_reviews"] >= 0
    
    def test_get_profile_stats_no_reviews(self, test_user, test_token):
        """Test stats for user with no reviews."""
        response = client.get(
            "/api/profile/stats",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_reviews"] == 0
        assert data["last_review_date"] is None
    
    def test_get_profile_stats_missing_auth(self):
        """Test stats retrieval without auth header."""
        response = client.get("/api/profile/stats")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_profile_stats_invalid_token(self):
        """Test stats retrieval with invalid token."""
        response = client.get(
            "/api/profile/stats",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProfileDataPersistence:
    """Tests for profile data persistence."""
    
    def test_profile_data_persists_after_update(self, test_user, test_token):
        """Test that profile updates persist across requests."""
        # Update profile
        update_data = {
            "full_name": "Persistent Name",
            "bio": "Persistent bio"
        }
        response = client.put(
            "/api/profile",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Retrieve profile again
        response = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Persistent Name"
        assert data["bio"] == "Persistent bio"
    
    def test_profile_timestamps_updated(self, test_user, test_token):
        """Test that profile_updated_at is set after update."""
        # Get initial profile
        response = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        initial_data = response.json()
        initial_updated_at = initial_data.get("profile_updated_at")
        
        # Update profile
        client.put(
            "/api/profile",
            json={"full_name": "Updated"},
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        # Get updated profile
        response = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        updated_data = response.json()
        updated_updated_at = updated_data.get("profile_updated_at")
        
        # Timestamp should be set
        assert updated_updated_at is not None
        # It should be newer than initial
        if initial_updated_at:
            assert updated_updated_at >= initial_updated_at


class TestProfileErrorMessages:
    """Tests for profile error message safety."""
    
    def test_error_messages_are_generic(self, test_token):
        """Test that error messages don't leak internal details."""
        # Try to update with invalid data
        response = client.put(
            "/api/profile",
            json={"bio": "x" * 501},
            headers={"Authorization": f"Bearer {test_token}"}
        )
        # Error message should not contain file paths, IDs, or internal details
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]
        error_msg = response.json()
        # Should not contain common path indicators
        assert "\\" not in str(error_msg).lower()
        assert "/src/" not in str(error_msg)
