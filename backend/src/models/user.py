"""
User model for authentication.
Supporting feature: Authentication & persistence layer.
"""
from sqlalchemy import Column, Integer, String, DateTime, Index, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database import Base


class User(Base):
    """
    User account model for literature review application.
    Stores user credentials and profile metadata for single-user review persistence.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Unique email for login identification
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Argon2-hashed password
    hashed_password = Column(String(255), nullable=False)
    
    # Optional user display name
    full_name = Column(String(255), nullable=True)
    
    # Profile fields (Phase 3.1 enhancement)
    bio = Column(String(500), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    profile_updated_at = Column(DateTime, nullable=True)
    
    # Relationship to saved reviews (cascade delete when user deleted)
    saved_reviews = relationship(
        "SavedReview",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Index for efficient email lookups during login
    __table_args__ = (
        Index("idx_users_email", "email"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"
