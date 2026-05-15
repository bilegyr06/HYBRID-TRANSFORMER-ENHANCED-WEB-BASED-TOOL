from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.core.database import init_db
from src.api.routes import router as api_router
from src.api.auth_routes import router as auth_router
from src.api.analysis_routes import router as analysis_router
from src.api.review_routes import router as review_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create required directories and initialize database on application startup.
    Supporting feature: Authentication & persistence layer for user account and review storage.
    """
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize database tables (supporting feature: user authentication & review persistence)
    init_db()
    
    yield
    # No cleanup needed on shutdown for this use case

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hybrid TextRank + BART Literature Review Assistant",
    lifespan=lifespan
)

# CORS for React frontend (we'll connect it next)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes (registration, login, logout, /me)
app.include_router(auth_router)

# Include review routes (save, list, get, delete)
app.include_router(review_router)

# Include analysis routes (additive unified analysis endpoint)
app.include_router(analysis_router, prefix="/api")

# Include API routes (upload, process, reviews)
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Literature Review Assistant Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
