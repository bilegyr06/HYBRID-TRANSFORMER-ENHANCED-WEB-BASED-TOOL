from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create required directories on application startup.
    """
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Literature Review Assistant Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)