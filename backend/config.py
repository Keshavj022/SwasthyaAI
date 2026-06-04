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

    # --- Local Health AI model integration (Task 12) ---
    # Hugging Face auth + cache for gated HAI-DEF weights. Loaded from .env;
    # NEVER commit the token. Required ONCE to download gated models.
    HF_TOKEN: str = ""
    HF_HOME: Path = MODELS_DIR / ".hf_cache"
    HF_HUB_OFFLINE: bool = True       # never hit the network after first download
    TRANSFORMERS_OFFLINE: bool = True

    # Real Hugging Face repo ids (must match the local snapshot dirs)
    MEDGEMMA_REPO_ID: str = "google/medgemma-4b-it"      # multimodal: text + image
    MEDSIGLIP_REPO_ID: str = "google/medsiglip-448"      # zero-shot image classifier
    # Voice: Whisper is the robust, non-gated default. For the gated
    # google/medasr set MEDASR_REPO_ID accordingly AND install transformers>=5
    # (see MODELS_SETUP.md). Whisper works with the pinned transformers<5.
    MEDASR_REPO_ID: str = "openai/whisper-large-v3-turbo"

    # Per-model enable flags. Leave False until the weights are downloaded;
    # when False (or weights/deps missing) the inference layer returns stubs.
    MEDGEMMA_MODE: bool = False
    MEDSIGLIP_MODE: bool = False
    MEDASR_MODE: bool = False

    # Inference dtype + generation limits (auto: bf16 on cuda/mps, fp32 on cpu)
    MODEL_DTYPE: str = "auto"  # 'auto' | 'bfloat16' | 'float16' | 'float32'
    MEDGEMMA_MAX_NEW_TOKENS: int = 512
    MEDASR_CHUNK_LENGTH_S: int = 20
    MEDASR_STRIDE_LENGTH_S: int = 2

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


# ---------------------------------------------------------------------------
# Export Hugging Face env vars so transformers / huggingface_hub honor offline
# mode and gated auth without per-call wiring. Guard empties so nothing leaks.
# ---------------------------------------------------------------------------
import os as _os

_os.environ.setdefault("HF_HOME", str(settings.HF_HOME))
if settings.HF_HUB_OFFLINE:
    _os.environ["HF_HUB_OFFLINE"] = "1"
    _os.environ["TRANSFORMERS_OFFLINE"] = "1"
if settings.HF_TOKEN:
    _os.environ["HF_TOKEN"] = settings.HF_TOKEN
# Prevent macOS OpenMP / tokenizer mutex deadlocks under uvicorn reload.
_os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


# ---------------------------------------------------------------------------
# Fail-fast security check: in non-development environments, refuse to boot
# with placeholder secrets (prevents shipping a forgeable JWT signing key).
# ---------------------------------------------------------------------------
_PLACEHOLDER_SECRETS = {
    "CHANGE-THIS-IN-PRODUCTION-USE-SECRETS-MANAGER",
    "swasthya-jwt-secret-change-in-prod",
    "your-secret-key-here",
}


def assert_secrets_configured() -> None:
    """Raise if running outside development with default/placeholder secrets."""
    if settings.ENVIRONMENT.lower() in {"development", "dev", "test", "testing"}:
        return
    bad = []
    if settings.SECRET_KEY in _PLACEHOLDER_SECRETS:
        bad.append("SECRET_KEY")
    if settings.JWT_SECRET in _PLACEHOLDER_SECRETS:
        bad.append("JWT_SECRET")
    if bad:
        raise RuntimeError(
            f"Refusing to start in ENVIRONMENT='{settings.ENVIRONMENT}' with "
            f"placeholder secret(s): {', '.join(bad)}. Set strong random values "
            f"in backend/.env before deploying."
        )
