from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "Automated Literature Review Assistant"
    VERSION: str = "0.1.0"
    DATA_DIR: Path = Path("data/raw")
    UPLOAD_DIR: Path = Path("data/uploads")
    MODEL_NAME: str = "facebook/bart-base"   # we can change to distilbart later

    class Config:
        env_file = ".env"

settings = Settings()