"""
FastAPI dependency injection for authentication.
Supporting feature: JWT token validation and user identification.
"""
from fastapi import Depends, HTTPException, Cookie, status
from sqlalchemy.orm import Session
from typing import Optional
from src.core.database import get_db
from src.models.user import User
from src.services.auth_service import decode_access_token


async def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Cookie(None, alias="access_token")
) -> User:
    """
    FastAPI dependency to extract and validate the current authenticated user from JWT cookie.
    
    Raises:
        HTTPException(401): If no token provided or token is invalid/expired
        HTTPException(404): If user_id from token not found in database
    
    Returns:
        User object from database
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode and validate JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from token claims
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format.",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Token may be for a deleted account.",
        )
    
    return user


async def get_current_user_optional(
    db: Session = Depends(get_db),
    token: Optional[str] = Cookie(None, alias="access_token")
) -> Optional[User]:
    """
    FastAPI dependency to extract current user if authenticated, but don't raise error if not.
    Used for endpoints that work with or without authentication.
    
    Returns:
        User object if authenticated, None otherwise
    """
    if not token:
        return None
    
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    try:
        user_id = int(user_id)
    except ValueError:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user
