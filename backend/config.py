"""
Application configuration.
Designed for offline-first operation.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Offline-First Hospital AI System"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS - Allow Next.js frontend
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_PATH: str = "../database/hospital.db"

    # Security
    SECRET_KEY: str = "CHANGE-THIS-IN-PRODUCTION-USE-SECRETS-MANAGER"

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
