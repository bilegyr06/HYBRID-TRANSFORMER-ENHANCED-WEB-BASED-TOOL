"""
Pydantic request/response schemas for literature review persistence endpoints.
Supporting feature: Authentication & persistence layer for saving user reviews.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


class SaveReviewRequest(BaseModel):
    """Request schema for saving a literature review with summarization results."""
    title: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional user-provided review title"
    )
    input_abstracts_count: int = Field(
        ...,
        gt=0,
        description="Count of input abstracts/documents processed"
    )
    extractive_summary: str = Field(
        ...,
        description="Extractive summary from TextRank pipeline"
    )
    abstractive_summary: str = Field(
        ...,
        description="Abstractive summary from fine-tuned BART/T5 model"
    )
    key_themes: Optional[list[str]] = Field(
        default=None,
        description="Array of key themes/keywords extracted from abstracts"
    )
    visualizations_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Metadata about visualizations (chart IDs, URLs, etc.)"
    )
    rouge_scores: Optional[dict[str, float]] = Field(
        default=None,
        description="ROUGE evaluation metrics (rouge1, rouge2, rougeL)"
    )


class SavedReviewResponse(BaseModel):
    """Response schema for a saved literature review."""
    id: int
    user_id: int
    title: Optional[str]
    input_abstracts_count: int
    extractive_summary: str
    abstractive_summary: str
    key_themes: Optional[list[str]]
    visualizations_metadata: Optional[dict[str, Any]]
    rouge_scores: Optional[dict[str, float]]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}  # Enable ORM mode for SQLAlchemy models


class SavedReviewListResponse(BaseModel):
    """Response schema for paginated list of saved reviews."""
    id: int
    title: Optional[str]
    input_abstracts_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PaginatedReviewsResponse(BaseModel):
    """Response schema for paginated review list with metadata."""
    reviews: list[SavedReviewListResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool
