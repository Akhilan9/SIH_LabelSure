import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

# Base workspace directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "APEX LabelSure"
    PROJECT_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Environment & Host
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    
    # Database: default to local sqlite in storage for zero-dependency local execution,
    # or use PostgreSQL when DATABASE_URL is set (e.g. in docker-compose).
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR}/storage/labelsure.db"
    )
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-apex-labelsure-jwt-key-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Storage
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = BASE_DIR / "storage" / "uploads"
    PROCESSED_DIR: Path = BASE_DIR / "storage" / "processed"
    REPORTS_DIR: Path = BASE_DIR / "storage" / "reports"
    RULES_DIR: Path = BASE_DIR / "rules"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    # AI / OCR Configurations
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "rapidocr")
    MIN_QUALITY_SCORE: float = 0.55
    MIN_BLUR_SCORE: float = 80.0
    MIN_CONFIDENCE_THRESHOLD: float = 0.60

    model_config = {"case_sensitive": True}

settings = Settings()

# Ensure critical storage paths exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
