import os
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Project metadata
    PROJECT_NAME: str = "Automated Literature Review Assistant"
    VERSION: str = "0.1.0"
    
    # File paths
    DATA_DIR: Path = Path("data/raw")
    UPLOAD_DIR: Path = Path("data/uploads")
    
    # File upload limits (Security: DoS prevention)
    MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100MB max per file
    MAX_TOTAL_UPLOAD_SIZE_BYTES: int = 500 * 1024 * 1024  # 500MB per request
    
    # NLP models
    MODEL_NAME: str = "facebook/bart-base"   # we can change to distilbart later
    
    # Database configuration
    # Supporting feature: Authentication & persistence layer
    # Default to SQLite for development; can switch to PostgreSQL via DATABASE_URL env var
    DATABASE_URL: str = "sqlite:///./litreview.db"
    
    # Database connection pooling (Scalability: prevent connection exhaustion)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True  # Verify connections before reuse
    
    # JWT authentication settings
    # Supporting feature: Authentication & persistence layer
    # CRITICAL: JWT_SECRET_KEY must be set via environment variable for security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24  # 24 hours (reduced from 1 year for security)
    
    # Cookie security settings (HTTPS/SameSite)
    # For production: override with COOKIE_SECURE=true via .env
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")

    # Frontend origins allowed to call the API.
    FRONTEND_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # Environment detection (for conditional security rules)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # production | development | testing

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        """CRITICAL: Ensure JWT_SECRET_KEY is set and not the default."""
        if not value or value == "your-secret-key-change-in-production":
            raise ValueError(
                "CRITICAL: JWT_SECRET_KEY environment variable must be set to a secure value. "
                "Do not use the default key in production."
            )
        if len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long for security")
        return value

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none")
        return normalized

    def __init__(self, **data):
        super().__init__(**data)
        # Validate production security requirements
        if self.ENVIRONMENT == "production":
            if not self.COOKIE_SECURE:
                raise ValueError("COOKIE_SECURE must be True in production")
            if self.COOKIE_SAMESITE.lower() != "strict":
                raise ValueError("COOKIE_SAMESITE must be 'strict' in production")

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.FRONTEND_ORIGINS.split(",")
            if origin.strip()
        ]

    class Config:
        env_file = ".env"

settings = Settings()
