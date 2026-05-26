"""
Authentication API endpoints for user registration, login, and session management.
Supporting feature: Authentication & persistence layer for user account management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime
from src.core.config import settings
from src.core.database import get_db
from src.core.error_handler import handle_error, handle_database_error
from src.core.rate_limiting import limiter, LOGIN_RATE_LIMIT, REGISTER_RATE_LIMIT
from src.models.user import User
from src.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token
)
from src.services.email_validation_service import EmailValidator
from src.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from src.api.dependencies import get_current_user

router = APIRouter(tags=["Authentication"], prefix="/auth")


def set_access_token_cookie(response: Response, access_token: str) -> None:
    """Store the JWT in the cookie used by auth dependencies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_EXPIRATION_HOURS * 60 * 60,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(REGISTER_RATE_LIMIT)
async def register(request: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **email**: Unique email address for login (must not be disposable)
    - **password**: Password (minimum 8 characters) — hashed with Argon2
    - **full_name**: User's display name
    
    Returns JWT token in secure httpOnly cookie on success.
    Raises 409 Conflict if email already registered.
    Raises 400 Bad Request if email is invalid or disposable.
    """
    # Phase 3.2: Validate email with enhanced checks
    is_valid, validation_error = EmailValidator.validate_for_registration(request.email, strict=True)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error
        )
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered. Please login or use a different email.",
        )
    
    # Create new user with hashed password
    hashed_pw = hash_password(request.password)
    new_user = User(
        email=request.email,
        hashed_password=hashed_pw,
        full_name=request.full_name,
        created_at=datetime.utcnow()
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise handle_database_error(
            e,
            "register new user",
            client_message="Failed to create account. Please try again."
        )
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    set_access_token_cookie(response, access_token)
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(LOGIN_RATE_LIMIT)
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    - **email**: Registered email
    - **password**: Account password
    
    On success, JWT token is set in secure httpOnly cookie.
    Raises 401 Unauthorized if credentials invalid.
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    
    # Update last_login timestamp
    try:
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise handle_database_error(
            e,
            "update user last_login",
            client_message="Login successful but failed to update session. Please try again."
        )
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    set_access_token_cookie(response, access_token)
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing authentication cookie.
    
    Frontend should also clear any localStorage tokens.
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.
    
    Protected endpoint — requires valid JWT token in cookie.
    Returns user ID, email, full name, and account timestamps.
    """
    return UserResponse.model_validate(current_user)
