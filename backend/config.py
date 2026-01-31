"""
Application configuration.
Designed for offline-first operation.
"""

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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
