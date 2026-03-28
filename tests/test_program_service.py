"""
Integration tests for ProgramService.
Uses a MockDetector (no OpenCV needed) to validate the full pipeline.
"""

from __future__ import annotations

from typing import List
from unittest.mock import MagicMock

import numpy as np
import pytest

from backend.commands import CommandFactory
from backend.detection import BaseBlockDetector, BlockSorter
from backend.models import BlockType, BoundingBox, DetectedBlock
from backend.services.program_service import ProgramService


class MockDetector(BaseBlockDetector):
    """Returns a hardcoded block list — no image processing."""

    def __init__(self, blocks: List[DetectedBlock]) -> None:
        self._blocks = blocks

    def detect(self, image: np.ndarray) -> List[DetectedBlock]:
        return self._blocks

    def detect_from_bytes(self, image_bytes: bytes) -> List[DetectedBlock]:
        return self._blocks  # ignore bytes entirely


def _block(btype: BlockType, x: int, y: int, loop_count=None) -> DetectedBlock:
    return DetectedBlock(
        block_type=btype,
        bounding_box=BoundingBox(x=x, y=y, width=60, height=60),
        confidence=1.0,
        loop_count=loop_count,
    )


class TestProgramService:
    def _service(self, blocks: List[DetectedBlock]) -> ProgramService:
        return ProgramService(
            detector=MockDetector(blocks),
            sorter=BlockSorter(),
            factory=CommandFactory(),
        )

    def test_returns_steps_for_simple_sequence(self):
        blocks = [
            _block(BlockType.START, x=0, y=0),
            _block(BlockType.MOVE_UP, x=80, y=0),
            _block(BlockType.MOVE_RIGHT, x=160, y=0),
        ]
        result = self._service(blocks).analyze_image(b"fake")
        assert result.success is True
        assert [s.action for s in result.steps] == ["move_up", "move_right"]

    def test_empty_detection_returns_warning(self):
        result = self._service([]).analyze_image(b"fake")
        assert result.success is True
        assert result.steps == []
        assert result.error is not None

    def test_raw_blocks_list_is_correct(self):
        blocks = [
            _block(BlockType.START, x=0, y=0),
            _block(BlockType.MOVE_DOWN, x=80, y=0),
        ]
        result = self._service(blocks).analyze_image(b"fake")
        assert "start" in result.raw_blocks
        assert "move_down" in result.raw_blocks

    def test_loop_expands_correctly(self):
        blocks = [
            _block(BlockType.START, x=0, y=0),
            _block(BlockType.LOOP_START, x=80, y=0, loop_count=3),
            _block(BlockType.MOVE_LEFT, x=160, y=0),
            _block(BlockType.LOOP_END, x=240, y=0),
        ]
        result = self._service(blocks).analyze_image(b"fake")
        assert [s.action for s in result.steps] == ["move_left"] * 3

    def test_bad_image_bytes_returns_failure(self):
        class FailingDetector(BaseBlockDetector):
            def detect(self, image):
                raise RuntimeError("decode failed")

        service = ProgramService(detector=FailingDetector(), sorter=BlockSorter())
        result = service.analyze_image(b"not_an_image")
        assert result.success is False
        assert result.error is not None
