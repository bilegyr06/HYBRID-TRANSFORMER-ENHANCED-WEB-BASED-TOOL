"""
Database configuration and session management.
Supporting feature: Authentication & persistence layer for user-specific review storage.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from src.core.config import settings

# Create engine based on DATABASE_URL from config
# Includes connection pooling configuration for scalability
is_sqlite = "sqlite" in settings.DATABASE_URL
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    poolclass=None if is_sqlite else None,  # Use default pool for PostgreSQL
    pool_size=settings.DB_POOL_SIZE if not is_sqlite else 5,
    max_overflow=settings.DB_MAX_OVERFLOW if not is_sqlite else 10,
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # Verify connections before reuse
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
