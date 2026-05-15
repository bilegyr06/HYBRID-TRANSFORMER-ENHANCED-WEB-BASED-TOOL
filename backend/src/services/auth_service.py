"""
Authentication service for user registration, login, and JWT token management.
Supporting feature: Authentication & persistence layer for single-user account management.
"""
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from src.core.config import settings
import re

# Password hashing configuration using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def validate_password_strength(password: str) -> None:
    """
    Validate password meets security requirements.
    Argon2 supports long passwords, so we only enforce basic rules.
    
    Args:
        password: Plain-text password to validate
        
    Raises:
        ValueError: If password doesn't meet requirements
    """
    # Check length
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long')
    
    # Check complexity
    if not re.search(r'[A-Z]', password):
        raise ValueError('Password must contain at least one uppercase letter (A-Z)')
    if not re.search(r'[a-z]', password):
        raise ValueError('Password must contain at least one lowercase letter (a-z)')
    if not re.search(r'[0-9]', password):
        raise ValueError('Password must contain at least one digit (0-9)')


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using Argon2.
    
    Args:
        password: Plain-text password string
        
    Returns:
        Argon2-hashed password string
        
    Raises:
        ValueError: If password doesn't meet security requirements
    """
    # Validate strength before hashing
    validate_password_strength(password)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against an Argon2 hash.
    
    Args:
        plain_password: Plain-text password to verify
        hashed_password: Argon2-hashed password from database
        
    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing claims to encode (e.g., {"sub": user_id})
        expires_delta: Optional expiration time delta. If None, uses default from config.
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to configured JWT_EXPIRATION_HOURS (365 days for thesis project)
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded claims dictionary if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        # Token is invalid, expired, or cannot be decoded
        return None
