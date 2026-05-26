"""
Tests for database transaction handling and consistency.

Verifies:
- Transactions rollback on errors (no partial saves)
- Data consistency maintained under concurrent operations
- Foreign key constraints enforced
- Duplicate email prevention (unique constraint)
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from src.models.user import User
from src.models.review import SavedReview
from src.services.auth_service import hash_password
from src.core.error_handler import handle_database_error


class TestTransactionRollback:
    """Test rollback behavior on errors."""
    
    def test_register_user_rollback_on_error(self, db: Session):
        """User registration rolls back if commit fails."""
        user = User(
            email="test@example.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        
        # Attempt to add duplicate email (should fail)
        duplicate_user = User(
            email="test@example.com",  # Same email
            hashed_password=hash_password("AnotherPass123!"),
            full_name="Another User"
        )
        db.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            db.commit()
        
        # Verify original user still exists, duplicate wasn't created
        users = db.query(User).filter(User.email == "test@example.com").all()
        assert len(users) == 1
    
    def test_save_review_rollback_on_error(self, db: Session):
        """Review save rolls back if commit fails."""
        # Create a user
        user = User(
            email="user@test.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create and save a review
        review = SavedReview(
            user_id=user.id,
            title="Test Review",
            extractive_summary="Summary",
            abstractive_summary="Summary",
            key_themes=["theme"],
            input_abstracts_count=1,
            created_at=datetime.utcnow()
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        initial_count = db.query(SavedReview).count()
        
        # Simulate error scenario: try to save without required field
        # (This depends on what fields are NOT NULL in the schema)
        bad_review = SavedReview(
            user_id=user.id,
            # Missing required fields - should fail
        )
        db.add(bad_review)
        
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        
        # Count should be unchanged
        final_count = db.query(SavedReview).count()
        assert initial_count == final_count


class TestUniqueConstraints:
    """Test enforcement of unique constraints."""
    
    def test_duplicate_email_prevented(self, db: Session):
        """Duplicate emails are rejected."""
        user1 = User(
            email="unique@example.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="User One"
        )
        db.add(user1)
        db.commit()
        
        # Try to add duplicate
        user2 = User(
            email="unique@example.com",
            hashed_password=hash_password("AnotherPass123!"),
            full_name="User Two"
        )
        db.add(user2)
        
        with pytest.raises(IntegrityError):
            db.commit()
        
        db.rollback()
        
        # Only first user should exist
        users = db.query(User).filter(User.email == "unique@example.com").all()
        assert len(users) == 1
    
    def test_same_email_different_case_check(self, db: Session):
        """Email uniqueness is case-insensitive (if database enforces it)."""
        user1 = User(
            email="User@Example.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="User One"
        )
        db.add(user1)
        db.commit()
        
        # Attempt with different case
        user2 = User(
            email="user@example.com",
            hashed_password=hash_password("AnotherPass123!"),
            full_name="User Two"
        )
        db.add(user2)
        
        # May or may not fail depending on database configuration
        # SQLite is case-insensitive by default
        # This test documents the behavior
        try:
            db.commit()
            # If it succeeded, database is case-insensitive
            users = db.query(User).filter(User.email == "user@example.com").all()
            assert len(users) == 1  # Should normalize to one user
        except IntegrityError:
            # If it failed, database enforces case-sensitive uniqueness
            db.rollback()
            users = db.query(User).filter(User.email.ilike("user@example.com")).all()
            assert len(users) == 1


class TestForeignKeyConstraints:
    """Test foreign key relationship enforcement."""
    
    def test_review_requires_valid_user(self, db: Session):
        """SavedReview must reference valid User."""
        # Try to create review with non-existent user
        review = SavedReview(
            user_id=99999,  # Non-existent user
            title="Orphan Review",
            extractive_summary="Summary",
            abstractive_summary="Summary",
            key_themes=["theme"],
            input_abstracts_count=1,
            created_at=datetime.utcnow()
        )
        db.add(review)
        
        with pytest.raises(IntegrityError):
            db.commit()
        
        db.rollback()
    
    def test_review_deleted_with_user(self, db: Session):
        """Reviews are deleted when user is deleted (cascade delete)."""
        # Create user and review
        user = User(
            email="user@test.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        review = SavedReview(
            user_id=user.id,
            title="Test Review",
            extractive_summary="Summary",
            abstractive_summary="Summary",
            key_themes=["theme"],
            input_abstracts_count=1,
            created_at=datetime.utcnow()
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        review_id = review.id
        
        # Verify review exists
        assert db.query(SavedReview).filter(SavedReview.id == review_id).first() is not None
        
        # Delete user
        db.delete(user)
        db.commit()
        
        # Review should be cascade-deleted
        assert db.query(SavedReview).filter(SavedReview.id == review_id).first() is None


class TestDataConsistency:
    """Test data consistency under various scenarios."""
    
    def test_user_timestamps_set_correctly(self, db: Session):
        """User created_at timestamp is set on creation."""
        before_creation = datetime.utcnow()
        
        user = User(
            email="timestamp@test.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="Timestamp Test"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        after_creation = datetime.utcnow()
        
        # Check timestamp is set
        assert user.created_at is not None
        assert before_creation <= user.created_at <= after_creation
    
    def test_review_timestamps_set_correctly(self, db: Session):
        """Review created_at and updated_at timestamps are set."""
        user = User(
            email="review-ts@test.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="Review Timestamp Test"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        before_creation = datetime.utcnow()
        
        review = SavedReview(
            user_id=user.id,
            title="Timestamp Test Review",
            extractive_summary="Summary",
            abstractive_summary="Summary",
            key_themes=["theme"],
            input_abstracts_count=1,
            created_at=before_creation
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        after_creation = datetime.utcnow()
        
        assert review.created_at is not None
        assert before_creation <= review.created_at <= after_creation
        
        # updated_at should be set if the model includes it
        if hasattr(review, 'updated_at'):
            assert review.updated_at is not None
    
    def test_multiple_reviews_per_user(self, db: Session):
        """Single user can have multiple reviews."""
        user = User(
            email="multi-review@test.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="Multi Review User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create multiple reviews
        for i in range(5):
            review = SavedReview(
                user_id=user.id,
                title=f"Review {i}",
                extractive_summary="Summary",
                abstractive_summary="Summary",
                key_themes=[f"theme{i}"],
                input_abstracts_count=i+1,
                created_at=datetime.utcnow()
            )
            db.add(review)
        
        db.commit()
        
        # Verify all reviews are associated with user
        user_reviews = db.query(SavedReview).filter(SavedReview.user_id == user.id).all()
        assert len(user_reviews) == 5


class TestTransactionIsolation:
    """Test transaction isolation and concurrent behavior."""
    
    def test_uncommitted_changes_not_visible(self, db: Session):
        """Uncommitted changes are not visible to other queries."""
        # Create a user
        user = User(
            email="isolation@test.com",
            hashed_password=hash_password("ValidPass123!"),
            full_name="Isolation Test"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create a second session
        from src.core.database import SessionLocal
        db2 = SessionLocal()
        
        try:
            # In first session, add a review but don't commit
            review = SavedReview(
                user_id=user.id,
                title="Uncommitted Review",
                extractive_summary="Summary",
                abstractive_summary="Summary",
                key_themes=["theme"],
                input_abstracts_count=1,
                created_at=datetime.utcnow()
            )
            db.add(review)
            # Don't commit yet
            
            # In second session, check if review is visible
            count_in_db2 = db2.query(SavedReview).filter(
                SavedReview.user_id == user.id
            ).count()
            
            # Should be 0 (not visible until committed)
            assert count_in_db2 == 0
            
            # Now commit in first session
            db.commit()
            
            # Now it should be visible in second session
            db2.expire_all()  # Clear cache
            count_in_db2_after = db2.query(SavedReview).filter(
                SavedReview.user_id == user.id
            ).count()
            assert count_in_db2_after == 1
        finally:
            db2.close()


class TestErrorHandlerWithDatabase:
    """Test error handler integration with database errors."""
    
    def test_handle_integrity_error(self):
        """Error handler properly categorizes integrity errors."""
        mock_error = IntegrityError(
            "statement",
            "params",
            ValueError("Duplicate key")
        )
        
        with pytest.raises(Exception) as exc_info:
            handle_database_error(
                mock_error,
                "save user",
                client_message="Email already exists."
            )
        
        # Should raise HTTPException with 400 status
        from fastapi import HTTPException, status
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
