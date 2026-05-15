"""
SavedReview model for user-specific review persistence.
Supporting feature: Authentication & persistence layer.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database import Base


class SavedReview(Base):
    """
    Persisted literature review tied to a user.
    Stores results from hybrid extractive-abstractive summarization pipeline:
    extractive summaries (TextRank), abstractive summaries (BART/T5),
    thematic clusters, and ROUGE evaluation metrics.
    
    Does NOT store full PDF/abstract text to conserve database storage.
    """
    __tablename__ = "saved_reviews"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to user account
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Optional user-provided title
    title = Column(String(500), nullable=True)
    
    # Count of input abstracts/documents processed
    input_abstracts_count = Column(Integer, nullable=False, default=1)
    
    # Full extractive summary from TextRank
    extractive_summary = Column(Text, nullable=True)
    
    # Full abstractive summary from fine-tuned BART/T5
    abstractive_summary = Column(Text, nullable=True)
    
    # Key themes/keywords extracted via TF-IDF as JSON array
    # Example: ["theme1", "theme2", "theme3", ...]
    key_themes = Column(JSON, nullable=True)
    
    # Metadata about visualizations (e.g., chart IDs, plot URLs) as JSON dict
    # Example: {"network_graph": "...", "theme_distribution": "..."}
    visualizations_metadata = Column(JSON, nullable=True)
    
    # ROUGE evaluation metrics as JSON dict
    # Example: {"rouge1": 0.45, "rouge2": 0.32, "rougeL": 0.42}
    rouge_scores = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user account
    owner = relationship("User", back_populates="saved_reviews")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_saved_reviews_user_id", "user_id"),
        Index("idx_saved_reviews_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<SavedReview(id={self.id}, user_id={self.user_id}, title='{self.title}', created_at={self.created_at})>"
