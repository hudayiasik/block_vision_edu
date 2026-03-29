"""
Centralized configuration.
Birden fazla Gemini API key destekler — rate limit'e ulaşınca otomatik döner.

.env örneği:
    GEMINI_API_KEY=key1,key2,key3
    GEMINI_MODEL=gemini-2.5-flash-lite
    DETECTOR_BACKEND=gemini
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BlockVision Edu"
    debug: bool = False

    max_upload_bytes: int = 10 * 1024 * 1024
    min_block_area_px: int = 1_500
    row_tolerance_px: int = 60
    cors_origins: list[str] = ["*"]

    # Virgülle ayrılmış birden fazla key: "key1,key2,key3"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    detector_backend: str = "gemini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def gemini_api_keys(self) -> List[str]:
        """Virgülle ayrılmış keyleri liste olarak döndür."""
        keys = [k.strip() for k in self.gemini_api_key.split(",") if k.strip()]
        return keys

    @property
    def effective_detector(self) -> str:
        if self.detector_backend == "gemini" and not self.gemini_api_key:
            return "color"
        return self.detector_backend


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
