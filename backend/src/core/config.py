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
    
    # NLP models
    MODEL_NAME: str = "facebook/bart-base"   # we can change to distilbart later
    
    # Database configuration
    # Supporting feature: Authentication & persistence layer
    # Default to SQLite for development; can switch to PostgreSQL via DATABASE_URL env var
    DATABASE_URL: str = "sqlite:///./litreview.db"
    
    # JWT authentication settings
    # Supporting feature: Authentication & persistence layer
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"  # Override via .env in production
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24 * 365  # 1 year (effectively non-expiring for thesis project)
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # Frontend origins allowed to call the API.
    FRONTEND_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none")
        return normalized

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
