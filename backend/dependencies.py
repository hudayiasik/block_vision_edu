from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from backend.commands import CommandFactory
from backend.config import Settings, get_settings
from backend.detection import BlockSorter, ColorBlockDetector
from backend.services.program_service import ProgramService


@lru_cache(maxsize=1)
def get_detector() -> ColorBlockDetector:
    settings = get_settings()
    return ColorBlockDetector(min_area=settings.min_block_area_px)


@lru_cache(maxsize=1)
def get_sorter() -> BlockSorter:
    settings = get_settings()
    return BlockSorter(row_tolerance=settings.row_tolerance_px)


def get_program_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProgramService:
    detector = get_detector()
    sorter = get_sorter()
    return ProgramService(detector=detector, sorter=sorter, factory=CommandFactory())