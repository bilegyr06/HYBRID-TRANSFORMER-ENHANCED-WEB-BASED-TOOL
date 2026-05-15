"""
Database configuration and session management.
Supporting feature: Authentication & persistence layer for user-specific review storage.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from src.core.config import settings

# Create engine based on DATABASE_URL from config
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False  # Set to True for SQL query logging in development
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency injection for database session.
    Yields a database session and ensures cleanup on request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize all database tables based on model definitions.
    Called on application startup via lifespan context.
    """
    Base.metadata.create_all(bind=engine)
