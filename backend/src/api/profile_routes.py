"""
User profile management endpoints (Phase 3.1).
Supporting feature: User profile persistence and management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import logging

from src.core.database import get_db
from src.core.error_handler import handle_error, handle_database_error, ClientError
from src.services.auth_service import decode_access_token
from src.schemas.auth import UserProfileResponse, ProfileUpdateRequest
from src.models.user import User
from src.models.review import SavedReview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["profile"])


def get_current_user(
    authorization: str | None = None,
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate current user from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authorization scheme")
        
        payload = decode_access_token(token)
        if not payload:
            raise ValueError("Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing user ID in token")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except ValueError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the complete profile of the authenticated user"
)
async def get_profile(
    authorization: str | None = None,
    db: Session = Depends(get_db)
) -> UserProfileResponse:
    """
    Get the authenticated user's profile information.
    
    **Authorization**: Required (Bearer token in Authorization header)
    
    **Returns**:
    - User profile with all metadata (bio, avatar, organization, etc.)
    
    **Raises**:
    - 401: Missing or invalid authorization token
    - 404: User not found
    """
    try:
        user = get_current_user(authorization, db)
        logger.info(f"Profile retrieved for user {user.id}")
        return UserProfileResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        error = handle_error(e, "profile_retrieval", 500, "Failed to retrieve profile")
        raise HTTPException(status_code=500, detail=error.message)


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    description="Update the authenticated user's profile information"
)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    authorization: str | None = None,
    db: Session = Depends(get_db)
) -> UserProfileResponse:
    """
    Update the authenticated user's profile information.
    
    **Authorization**: Required (Bearer token in Authorization header)
    
    **Request Body**:
    - full_name: Optional user display name
    - bio: Optional biography (max 500 chars)
    - avatar_url: Optional profile avatar URL
    - organization: Optional organization name
    
    **Returns**:
    - Updated user profile
    
    **Raises**:
    - 400: Invalid profile data
    - 401: Missing or invalid authorization token
    - 404: User not found
    - 500: Database error
    """
    try:
        user = get_current_user(authorization, db)
        
        # Update profile fields
        if profile_data.full_name is not None:
            user.full_name = profile_data.full_name
        if profile_data.bio is not None:
            user.bio = profile_data.bio
        if profile_data.avatar_url is not None:
            user.avatar_url = profile_data.avatar_url
        if profile_data.organization is not None:
            user.organization = profile_data.organization
        
        user.profile_updated_at = datetime.utcnow()
        
        try:
            db.commit()
            logger.info(f"Profile updated for user {user.id}")
            return UserProfileResponse.model_validate(user)
        except Exception as e:
            db.rollback()
            error = handle_database_error(e, "profile_update", "Failed to update profile")
            raise HTTPException(status_code=error.status_code, detail=error.message)
            
    except HTTPException:
        raise
    except Exception as e:
        error = handle_error(e, "profile_update", 500, "Failed to update profile")
        raise HTTPException(status_code=500, detail=error.message)


@router.get(
    "/profile/stats",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get user review statistics",
    description="Get statistics about the authenticated user's reviews"
)
async def get_profile_stats(
    authorization: str | None = None,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get user statistics including review count and last review date.
    
    **Authorization**: Required (Bearer token in Authorization header)
    
    **Returns**:
    - total_reviews: Number of saved reviews
    - last_review_date: Timestamp of most recent review
    - account_age_days: Days since account creation
    
    **Raises**:
    - 401: Missing or invalid authorization token
    - 404: User not found
    """
    try:
        user = get_current_user(authorization, db)
        
        # Get review statistics
        review_count = db.query(func.count(SavedReview.id)).filter(
            SavedReview.owner_id == user.id
        ).scalar() or 0
        
        last_review = db.query(SavedReview).filter(
            SavedReview.owner_id == user.id
        ).order_by(SavedReview.created_at.desc()).first()
        
        account_age = (datetime.utcnow() - user.created_at).days
        
        logger.info(f"Profile stats retrieved for user {user.id}")
        
        return {
            "total_reviews": review_count,
            "last_review_date": last_review.created_at if last_review else None,
            "account_age_days": account_age,
            "member_since": user.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        error = handle_error(e, "stats_retrieval", 500, "Failed to retrieve statistics")
        raise HTTPException(status_code=500, detail=error.message)
