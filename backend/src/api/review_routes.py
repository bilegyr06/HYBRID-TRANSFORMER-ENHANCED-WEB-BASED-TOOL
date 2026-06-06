"""
API endpoints for saved literature review persistence with authentication.
Supporting feature: Database-backed review storage tied to authenticated users.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from src.core.database import get_db
from src.core.error_handler import handle_error, handle_database_error
from src.models.user import User
from src.models.review import SavedReview
from src.schemas.reviews import (
    SaveReviewRequest,
    SavedReviewResponse,
    PaginatedReviewsResponse,
    SavedReviewListResponse
)
from src.api.dependencies import get_current_user

router = APIRouter(tags=["Reviews"], prefix="/reviews")


def save_review_to_db(db: Session, current_user: User, request: SaveReviewRequest) -> SavedReview:
    """Persist a review for the authenticated user and return the ORM object."""
    new_review = SavedReview(
        user_id=current_user.id,
        title=request.title,
        input_abstracts_count=request.input_abstracts_count,
        extractive_summary=request.extractive_summary,
        abstractive_summary=request.abstractive_summary,
        key_themes=request.key_themes,
        visualizations_metadata=request.visualizations_metadata,
        rouge_scores=request.rouge_scores or request.quality_metrics,
        quality_metrics=request.quality_metrics,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    try:
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
    except Exception as e:
        db.rollback()
        raise handle_database_error(
            e,
            "save review to database",
            client_message="Failed to save review. Please try again."
        )
    return new_review


@router.post("/save", response_model=SavedReviewResponse, status_code=status.HTTP_201_CREATED)
async def save_review(
    request: SaveReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a literature review with summarization results to database.
    
    This endpoint stores extractive summaries, abstractive summaries, 
    key themes, and ROUGE evaluation metrics linked to the current user.
    
    Protected endpoint — requires JWT authentication.
    
    Args:
        title: Optional title for the review
        extractive_summary: Extractive summary from TextRank
        abstractive_summary: Abstractive summary from BART/T5
        key_themes: Array of extracted themes/keywords
        visualizations_metadata: Metadata about visualizations
        rouge_scores: ROUGE evaluation metrics
        input_abstracts_count: Number of input documents processed
    
    Returns:
        SavedReviewResponse with new review ID and metadata
    """
    new_review = save_review_to_db(db, current_user, request)
    return SavedReviewResponse.model_validate(new_review)


@router.get("/", response_model=PaginatedReviewsResponse)
async def list_user_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    List all saved reviews for the authenticated user.
    
    Protected endpoint — requires JWT authentication.
    
    Returns paginated list of user's saved reviews with pagination metadata.
    Sorted by creation date (newest first).
    
    Query Parameters:
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
    
    Returns:
        PaginatedReviewsResponse with reviews and pagination info
    """
    # Get total count of reviews for this user
    total_count = db.query(SavedReview).filter(SavedReview.user_id == current_user.id).count()
    
    # Calculate offset for pagination
    offset = (page - 1) * page_size
    
    # Query reviews for this user, sorted by created_at descending (newest first)
    reviews = (
        db.query(SavedReview)
        .filter(SavedReview.user_id == current_user.id)
        .order_by(SavedReview.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    
    # Convert to response schema (excludes full summary text for list view)
    review_list = [SavedReviewListResponse.model_validate(r) for r in reviews]
    
    # Calculate if there are more pages
    has_more = (offset + page_size) < total_count
    
    return PaginatedReviewsResponse(
        reviews=review_list,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{review_id}", response_model=SavedReviewResponse)
async def get_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific saved review.
    
    Protected endpoint — requires JWT authentication.
    Only the review owner can access their review.
    
    Args:
        review_id: ID of the review to retrieve
    
    Returns:
        SavedReviewResponse with full review details
    
    Raises:
        404: Review not found
        403: Review belongs to a different user (unauthorized)
    """
    review = db.query(SavedReview).filter(SavedReview.id == review_id).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found."
        )
    
    # Verify ownership
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    
    return SavedReviewResponse.model_validate(review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a saved review.
    
    Protected endpoint — requires JWT authentication.
    Only the review owner can delete their review.
    
    Args:
        review_id: ID of the review to delete
    
    Raises:
        404: Review not found
        403: Review belongs to a different user (unauthorized)
    """
    review = db.query(SavedReview).filter(SavedReview.id == review_id).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found."
        )
    
    # Verify ownership
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this resource."
        )
    
    # Delete the review
    try:
        db.delete(review)
        db.commit()
    except Exception as e:
        db.rollback()
        raise handle_database_error(
            e,
            "delete review",
            client_message="Failed to delete review. Please try again."
        )
    
    return None  # 204 No Content
