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
