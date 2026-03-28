"""
Centralized configuration.

All secrets and settings are read from environment variables or a .env file.
NEVER hardcode API keys in source code — always use env vars.

Usage:
    Local dev  → create a .env file (git-ignored)
    Production → set env vars in Render / Railway dashboard
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BlockVision Edu"
    debug: bool = False

    # Upload limits
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # Detection (ColorBlockDetector fallback tuning)
    min_block_area_px: int = 1_500
    row_tolerance_px: int = 60

    # CORS
    cors_origins: list[str] = ["*"]

    # Gemini — set GEMINI_API_KEY in .env or hosting dashboard
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Which detector to use: "gemini" | "color"
    detector_backend: str = "gemini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def effective_detector(self) -> str:
        if self.detector_backend == "gemini" and not self.gemini_api_key:
            return "color"
        return self.detector_backend


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
