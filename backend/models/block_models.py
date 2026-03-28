"""
Domain models for physical code blocks.
Immutable dataclasses ensure thread-safety and predictability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class BlockType(str, Enum):
    """All recognizable physical block types."""

    START = "start"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    UNKNOWN = "unknown"

    # --------------- helpers ---------------

    @property
    def is_movement(self) -> bool:
        return self in {
            BlockType.MOVE_UP,
            BlockType.MOVE_DOWN,
            BlockType.MOVE_LEFT,
            BlockType.MOVE_RIGHT,
        }

    @property
    def is_control(self) -> bool:
        return self in {BlockType.LOOP_START, BlockType.LOOP_END}


@dataclass(frozen=True)
class BoundingBox:
    """Pixel bounding box of a detected block in the image."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def grid_row(self) -> int:
        """Coarse row index used for reading-order sort."""
        return self.y // 80  # buckets of 80 px

    @property
    def grid_col(self) -> int:
        return self.x // 80


@dataclass(frozen=True)
class DetectedBlock:
    """A single block found by the vision layer."""

    block_type: BlockType
    bounding_box: BoundingBox
    confidence: float
    loop_count: Optional[int] = None  # only meaningful for LOOP_START

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
        if self.loop_count is not None and self.loop_count < 1:
            raise ValueError("loop_count must be >= 1")
