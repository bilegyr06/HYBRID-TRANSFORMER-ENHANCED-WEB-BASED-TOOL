"""
Pydantic request/response schemas for authentication endpoints.
Supporting feature: Authentication & persistence layer.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
import re


class RegisterRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr = Field(..., description="User email address (must be unique)")
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Password (8-72 characters, must contain uppercase, lowercase, and digits)"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's full name"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password complexity: must contain uppercase, lowercase, and digits."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Response schema for user account information."""
    id: int
    email: str
    full_name: str
    created_at: datetime
    last_login: datetime | None = None
    
    model_config = {"from_attributes": True}  # Enable ORM mode for SQLAlchemy models


class AuthResponse(BaseModel):
    """Response schema for successful authentication."""
    access_token: str = Field(..., description="JWT token for authenticated requests")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user info")


# Phase 3.1: User Profile Enhancement

class UserProfileResponse(BaseModel):
    """Complete user profile with extended metadata."""
    id: int
    email: str
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    organization: str | None = None
    is_active: bool = True
    created_at: datetime
    last_login: datetime | None = None
    profile_updated_at: datetime | None = None
    
    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""
    full_name: str | None = Field(
        None,
        max_length=255,
        description="User's full name"
    )
    bio: str | None = Field(
        None,
        max_length=500,
        description="Short biography (max 500 characters)"
    )
    avatar_url: str | None = Field(
        None,
        max_length=255,
        description="URL to profile avatar image"
    )
    organization: str | None = Field(
        None,
        max_length=255,
        description="Organization or institution name"
    )
    
    @field_validator('avatar_url')
    @classmethod
    def validate_avatar_url(cls, v: str | None) -> str | None:
        """Validate avatar URL format if provided."""
        if v is not None and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Avatar URL must start with http:// or https://')
        return v
