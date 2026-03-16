"""
Application configuration.
Designed for offline-first operation.
"""

import json
from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "SwasthyaAI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS - Allow Next.js frontend
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str = "sqlite:///../database/hospital.db"
    DATABASE_PATH: str = "../database/hospital.db"

    # Security
    SECRET_KEY: str = "CHANGE-THIS-IN-PRODUCTION-USE-SECRETS-MANAGER"

    # JWT
    JWT_SECRET: str = "swasthya-jwt-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # AI / Gemini
    GEMINI_API_KEY: str = "your-gemini-api-key-here"
    OFFLINE_MODE: bool = True

    # AI Model Paths (offline-first: models stored locally)
    MODELS_DIR: Path = Path(__file__).parent.parent / "models"
    MEDGEMMA_MODEL_PATH: Path = MODELS_DIR / "medgemma"
    MEDSIGCLIP_MODEL_PATH: Path = MODELS_DIR / "medsigLIP"
    MEDASR_MODEL_PATH: Path = MODELS_DIR / "medasr"

    # AI Model Configuration
    USE_GPU: bool = False  # Auto-detected at runtime
    MODEL_DEVICE: str = "auto"  # 'auto', 'cpu', 'cuda', or 'mps'
    MAX_GENERATION_LENGTH: int = 512
    TEMPERATURE: float = 0.7

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Auto-detect GPU availability (CUDA → MPS → CPU)
try:
    import torch
    if torch.cuda.is_available():
        settings.USE_GPU = True
        if settings.MODEL_DEVICE == "auto":
            settings.MODEL_DEVICE = "cuda"
    elif torch.backends.mps.is_available():
        settings.USE_GPU = True
        if settings.MODEL_DEVICE == "auto":
            settings.MODEL_DEVICE = "mps"
    else:
        settings.USE_GPU = False
        if settings.MODEL_DEVICE == "auto":
            settings.MODEL_DEVICE = "cpu"
except ImportError:
    settings.USE_GPU = False
    settings.MODEL_DEVICE = "cpu"
