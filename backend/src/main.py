from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.core.database import init_db
from src.core.rate_limiting import setup_rate_limiting
from src.core.logging_config import setup_logging
from src.core.request_logging import setup_request_logging
from src.core.performance_metrics import setup_performance_metrics, get_metrics_instance
from src.api.routes import router as api_router
from src.api.auth_routes import router as auth_router
from src.api.analysis_routes import router as analysis_router
from src.api.review_routes import router as review_router
from src.api.profile_routes import router as profile_router
import logging
import os
from pathlib import Path

# Setup centralized logging (Phase 2.7)
setup_logging()
logger = logging.getLogger(__name__)

# Global model instances (initialized on startup)
_models_initialized = False

async def preload_ml_models():
    """Pre-load NLP models on application startup to prevent first-request latency.
    
    This solves the issue where the first request would block for 5-10 seconds
    while loading the BART and TextRank models. By pre-loading during startup,
    all subsequent requests are fast.
    """
    global _models_initialized
    if _models_initialized:
        return
    
    try:
        logger.info("Pre-loading NLP models (BART, TextRank)...")
        from src.services.summarizer_service import SummarizerService
        from src.services.text_rank_service_improved import TextRankService
        
        # Initialize services (this loads the models into memory)
        _ = SummarizerService()
        _ = TextRankService()
        
        _models_initialized = True
        logger.info("✓ NLP models pre-loaded successfully")
    except Exception as e:
        logger.error(f"Failed to pre-load NLP models: {e}", exc_info=True)
        raise  # Prevent app startup if models can't load

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Setup HuggingFace cache, create required directories, pre-load NLP models, and initialize database on startup.
    Supporting feature: Authentication & persistence layer for user account and review storage.
    """
    # Setup HuggingFace Hub cache directory (persists model downloads across restarts)
    hf_cache_dir = Path(settings.HF_HOME)
    hf_cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(hf_cache_dir.absolute())
    logger.info(f"HuggingFace cache directory: {hf_cache_dir.absolute()}")
    
    # Create required application directories
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Setup performance metrics (Phase 3.5)
    setup_performance_metrics()
    
    # Pre-load NLP models (CRITICAL for performance - downloads cached on first load)
    await preload_ml_models()
    
    # Initialize database tables (supporting feature: user authentication & review persistence)
    init_db()
    
    yield
    
    # Log final metrics on shutdown
    metrics = get_metrics_instance()
    metrics.log_summary()

# Phase 3.3: Swagger API Documentation tags
tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration, login, and session management. JWT tokens stored in secure httpOnly cookies.",
    },
    {
        "name": "profile",
        "description": "User profile management and statistics (Phase 3.1)",
    },
    {
        "name": "Reviews",
        "description": "Manage saved literature reviews including creation, retrieval, and deletion",
    },
    {
        "name": "Analysis",
        "description": "Document analysis endpoints for text extraction, summarization, and synthesis",
    },
    {
        "name": "Upload",
        "description": "File upload and document processing with security validation",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hybrid TextRank + BART Literature Review Assistant with advanced document analysis",
    openapi_tags=tags_metadata,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure rate limiting (Phase 2.6: Brute force protection)
setup_rate_limiting(app)

# Configure request/response logging (Phase 3.4: Request tracking and debugging)
setup_request_logging(app, slow_request_threshold_ms=1000)

# CORS for React frontend - use explicit methods/headers (Security: reduces attack surface)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Changed from ["*"] for security
    allow_headers=["Content-Type", "Authorization"],  # Changed from ["*"] for security
    expose_headers=["Content-Length"],
    max_age=3600,  # Cache CORS preflight response for 1 hour
)

# Include auth routes (registration, login, logout, /me)
app.include_router(auth_router)

# Include profile routes (Phase 3.1: user profile management)
app.include_router(profile_router)

# Include review routes (save, list, get, delete)
app.include_router(review_router)

# Include analysis routes (additive unified analysis endpoint)
app.include_router(analysis_router, prefix="/api")

# Include API routes (upload, process, reviews)
app.include_router(api_router, prefix="/api")

@app.get("/metrics", tags=["Monitoring"])
async def get_performance_metrics():
    """
    Get performance metrics for all endpoints (Phase 3.5).
    
    Returns timing statistics (min, max, avg, p50, p95, p99), error rates, and counts
    for each tracked endpoint. Useful for monitoring and performance analysis.
    
    **Returns**: Dictionary with endpoint metrics
    """
    metrics = get_metrics_instance()
    return metrics.get_metrics()


@app.get("/")
async def root():
    return {"message": "Literature Review Assistant Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
