"""Bot configuration settings."""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file only in development
# Railway provides environment variables directly, no .env file needed
if os.getenv("RAILWAY_ENVIRONMENT") is None:
    load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Application settings."""

    # Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")

    # Channel
    REQUIRED_CHANNEL: str = os.getenv("REQUIRED_CHANNEL", "@creometric")
    REQUIRED_CHANNEL_ID: int = int(os.getenv("REQUIRED_CHANNEL_ID", "0"))

    # Admin
    ADMIN_CHAT_ID: int = int(os.getenv("ADMIN_CHAT_ID", "0"))
    ADMIN_USER_IDS: List[int] = [
        int(uid) for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid
    ]

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "creo_bot")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Celery
    # Railway sets REDIS_URL, use it for both broker and backend if CELERY_* vars not set
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND") or os.getenv("REDIS_URL", "redis://localhost:6379/0").replace("/0", "/1")

    # File Limits (in MB)
    MAX_PHOTO_SIZE_MB: int = int(os.getenv("MAX_PHOTO_SIZE_MB", "20"))
    MAX_VIDEO_SIZE_MB: int = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))
    MAX_AUDIO_SIZE_MB: int = int(os.getenv("MAX_AUDIO_SIZE_MB", "50"))
    COMPRESSED_VIDEO_TARGET_MB: int = int(os.getenv("COMPRESSED_VIDEO_TARGET_MB", "20"))
    MAX_VIDEO_CIRCLE_DURATION: int = int(os.getenv("MAX_VIDEO_CIRCLE_DURATION", "60"))

    # Convert to bytes
    @property
    def MAX_PHOTO_SIZE_BYTES(self) -> int:
        return self.MAX_PHOTO_SIZE_MB * 1024 * 1024

    @property
    def MAX_VIDEO_SIZE_BYTES(self) -> int:
        return self.MAX_VIDEO_SIZE_MB * 1024 * 1024

    @property
    def MAX_AUDIO_SIZE_BYTES(self) -> int:
        return self.MAX_AUDIO_SIZE_MB * 1024 * 1024

    @property
    def COMPRESSED_VIDEO_TARGET_BYTES(self) -> int:
        return self.COMPRESSED_VIDEO_TARGET_MB * 1024 * 1024

    # Directories
    TEMP_DIR: Path = BASE_DIR / os.getenv("TEMP_DIR", "temp")
    LOG_DIR: Path = BASE_DIR / os.getenv("LOG_DIR", "logs")
    ASSETS_DIR: Path = BASE_DIR / os.getenv("ASSETS_DIR", "assets")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Sentry
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

    def __init__(self):
        """Create necessary directories."""
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    def validate(self) -> None:
        """Validate critical settings."""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set")


# Create settings instance
settings = Settings()
