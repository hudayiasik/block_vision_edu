"""
Centralized configuration.
All settings readable from environment variables or a .env file.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "BlockVision Edu"
    debug: bool = False

    # Image upload limits
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # Detection tuning
    min_block_area_px: int = 1_500
    row_tolerance_px: int = 60

    # CORS — set to your frontend origin in production
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return singleton Settings instance (cached after first call)."""
    return Settings()
