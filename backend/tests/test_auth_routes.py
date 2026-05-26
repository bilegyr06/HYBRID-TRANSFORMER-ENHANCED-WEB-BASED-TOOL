"""
Tests for API endpoint authorization and access control.

Verifies:
- Unauthenticated users cannot access protected endpoints
- Users cannot access/modify other users' resources
- Ownership checks are enforced
- Proper status codes returned (401, 403, 404)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from src.main import app
from src.core.database import get_db
from src.models.user import User
from src.models.review import SavedReview
from src.services.auth_service import hash_password, create_access_token
from tests.conftest import (
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    TEST_USER_FULL_NAME,
)


# Override database dependency for testing
def get_test_db():
    """Provide test database session."""
    from src.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = get_test_db
client = TestClient(app)


class TestAuthProtection:
    """Test that endpoints properly require authentication."""
    
    def test_save_review_requires_auth(self):
        """POST /reviews/save requires authentication."""
        response = client.post(
            "/reviews/save",
            json={
                "title": "Test Review",
                "extractive_summary": "Summary",
                "abstractive_summary": "Summary",
                "key_themes": ["theme1"],
                "input_abstracts_count": 1
            }
        )
        
        assert response.status_code == 401
        assert "authenticate" in response.json()["detail"].lower()
    
    def test_list_reviews_requires_auth(self):
        """GET /reviews requires authentication."""
        response = client.get("/reviews")
        
        assert response.status_code == 401
    
    def test_get_review_requires_auth(self):
        """GET /reviews/{id} requires authentication."""
        response = client.get("/reviews/1")
        
        assert response.status_code == 401
    
    def test_delete_review_requires_auth(self):
        """DELETE /reviews/{id} requires authentication."""
        response = client.delete("/reviews/1")
        
        assert response.status_code == 401


class TestReviewOwnershipEnforcement:
    """Test that users can only access their own reviews."""
    
    @pytest.fixture
    def auth_user(self, db: Session):
        """Create authenticated test user."""
        user = User(
            email="user1@test.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="User One"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @pytest.fixture
    def other_user(self, db: Session):
        """Create another test user."""
        user = User(
            email="user2@test.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="User Two"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @pytest.fixture
    def auth_user_review(self, db: Session, auth_user: User):
        """Create a review owned by auth_user."""
        review = SavedReview(
            user_id=auth_user.id,
            title="Auth User Review",
            extractive_summary="Summary",
            abstractive_summary="Summary",
            key_themes=["theme1"],
            input_abstracts_count=1,
            created_at=datetime.utcnow()
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review
    
    @pytest.fixture
    def other_user_review(self, db: Session, other_user: User):
        """Create a review owned by other_user."""
        review = SavedReview(
            user_id=other_user.id,
            title="Other User Review",
            extractive_summary="Summary",
            abstractive_summary="Summary",
            key_themes=["theme2"],
            input_abstracts_count=1,
            created_at=datetime.utcnow()
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review
    
    def test_get_own_review_succeeds(self, auth_user: User, auth_user_review: SavedReview):
        """User can retrieve their own review."""
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.get(
            f"/reviews/{auth_user_review.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["id"] == auth_user_review.id
    
    def test_get_other_user_review_forbidden(
        self, auth_user: User, other_user_review: SavedReview
    ):
        """User cannot retrieve another user's review."""
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.get(
            f"/reviews/{other_user_review.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_delete_own_review_succeeds(self, auth_user: User, auth_user_review: SavedReview):
        """User can delete their own review."""
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.delete(
            f"/reviews/{auth_user_review.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
    
    def test_delete_other_user_review_forbidden(
        self, auth_user: User, other_user_review: SavedReview
    ):
        """User cannot delete another user's review."""
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.delete(
            f"/reviews/{other_user_review.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_list_reviews_only_shows_own(self, auth_user: User, other_user: User, db: Session):
        """User's review list only includes their own reviews."""
        # Create reviews for both users
        user1_review = SavedReview(
            user_id=auth_user.id,
            title="User 1 Review",
            extractive_summary="Summary",
            abstractive_summary="Summary",
            key_themes=["theme"],
            input_abstracts_count=1,
            created_at=datetime.utcnow()
        )
        user2_review = SavedReview(
            user_id=other_user.id,
            title="User 2 Review",
            extractive_summary="Summary",
            abstractive_summary="Summary",
            key_themes=["theme"],
            input_abstracts_count=1,
            created_at=datetime.utcnow()
        )
        db.add(user1_review)
        db.add(user2_review)
        db.commit()
        
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.get(
            "/reviews",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        reviews = response.json()["reviews"]
        review_ids = [r["id"] for r in reviews]
        
        # Should only contain user1's review
        assert user1_review.id in review_ids
        assert user2_review.id not in review_ids


class TestResourceNotFoundHandling:
    """Test 404 responses for non-existent resources."""
    
    def test_get_nonexistent_review_returns_404(self, auth_user: User):
        """GET /reviews/9999 returns 404 without exposing ID."""
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.get(
            "/reviews/9999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        detail = response.json()["detail"]
        
        # Response should not expose the ID
        assert "9999" not in detail
    
    def test_delete_nonexistent_review_returns_404(self, auth_user: User):
        """DELETE /reviews/9999 returns 404."""
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.delete(
            "/reviews/9999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404


class TestErrorMessageSafety:
    """Test that error messages don't expose sensitive information."""
    
    def test_unauthorized_doesnt_expose_user_id(self):
        """401 error doesn't expose user ID or system details."""
        response = client.get("/reviews")
        
        detail = response.json()["detail"]
        # Should not contain any IDs or technical details
        assert not any(char.isdigit() for char in detail)
    
    def test_forbidden_doesnt_expose_resource_details(self, auth_user: User, other_user_review: SavedReview):
        """403 error doesn't expose resource ID or owner info."""
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.get(
            f"/reviews/{other_user_review.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        detail = response.json()["detail"]
        # Should not contain review ID
        assert str(other_user_review.id) not in detail
    
    def test_error_message_is_generic(self, auth_user: User, other_user_review: SavedReview):
        """Access denied error message is generic, not specific."""
        token = create_access_token(data={"sub": str(auth_user.id)})
        
        response = client.get(
            f"/reviews/{other_user_review.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        detail = response.json()["detail"]
        # Should be generic message, not "Review 5 belongs to user 2"
        assert "belongs to" not in detail.lower()
        assert "user" not in detail.lower()


class TestInvalidTokenHandling:
    """Test handling of malformed or invalid tokens."""
    
    def test_malformed_token_returns_401(self):
        """Malformed token returns 401."""
        response = client.get(
            "/reviews",
            headers={"Authorization": "Bearer not.a.valid.token"}
        )
        
        assert response.status_code == 401
    
    def test_expired_token_returns_401(self):
        """Expired token returns 401."""
        from datetime import timedelta
        
        # Create token that expires immediately
        past_delta = timedelta(seconds=-1)
        token = create_access_token(data={"sub": "123"}, expires_delta=past_delta)
        
        import time
        time.sleep(0.1)  # Ensure it's expired
        
        response = client.get(
            "/reviews",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 401
    
    def test_missing_bearer_prefix_returns_401(self):
        """Token without Bearer prefix returns 401."""
        token = create_access_token(data={"sub": "123"})
        
        response = client.get(
            "/reviews",
            headers={"Authorization": token}  # Missing "Bearer "
        )
        
        assert response.status_code == 401
    
    def test_missing_authorization_header_returns_401(self):
        """Missing Authorization header returns 401."""
        response = client.get("/reviews")
        
        assert response.status_code == 401
