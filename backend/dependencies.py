"""
Dependency injection — çoklu API key desteği ile.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from backend.commands import CommandFactory
from backend.config import Settings, get_settings
from backend.detection import BaseBlockDetector, BlockSorter, ColorBlockDetector, GeminiBlockDetector
from backend.services.program_service import ProgramService

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_detector() -> BaseBlockDetector:
    settings = get_settings()
    backend = settings.effective_detector

    if backend == "gemini":
        keys = settings.gemini_api_keys
        logger.info(
            "GeminiBlockDetector: %d key, model=%s",
            len(keys), settings.gemini_model
        )
        return GeminiBlockDetector(api_keys=keys, model=settings.gemini_model)

    logger.info("ColorBlockDetector (OpenCV fallback)")
    return ColorBlockDetector(min_area=settings.min_block_area_px)


@lru_cache(maxsize=1)
def get_sorter() -> BlockSorter:
    settings = get_settings()
    return BlockSorter(row_tolerance=settings.row_tolerance_px)


def get_program_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProgramService:
    return ProgramService(
        detector=get_detector(),
        sorter=get_sorter(),
        factory=CommandFactory(),
    )
