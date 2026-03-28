"""
Color profile for every physical block type.

Each block has a DISTINCT solid color so OpenCV HSV thresholding
can classify it reliably under typical indoor lighting.

Physical color guide (print and laminate on your blocks):
  START       → Bright Green   🟩
  MOVE_UP     → Blue           🔵
  MOVE_DOWN   → Red            🔴
  MOVE_LEFT   → Yellow         🟡
  MOVE_RIGHT  → Purple         🟣
  LOOP_START  → Orange         🟠  (number written on top indicates repeat count)
  LOOP_END    → Pink/Magenta   🩷
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from backend.models import BlockType

# HSV range: (H_low, S_low, V_low), (H_high, S_high, V_high)
HsvRange = Tuple[Tuple[int, int, int], Tuple[int, int, int]]


@dataclass(frozen=True)
class ColorProfile:
    block_type: BlockType
    lower: Tuple[int, int, int]
    upper: Tuple[int, int, int]
    # For red hue, OpenCV wraps around 180, so we need a second range
    lower2: Optional[Tuple[int, int, int]] = None
    upper2: Optional[Tuple[int, int, int]] = None


# fmt: off
COLOR_PROFILES: Dict[BlockType, ColorProfile] = {
    BlockType.START: ColorProfile(
        block_type=BlockType.START,
        lower=(40, 80, 80),
        upper=(80, 255, 255),
    ),
    BlockType.MOVE_UP: ColorProfile(
        block_type=BlockType.MOVE_UP,
        lower=(100, 100, 80),
        upper=(135, 255, 255),
    ),
    BlockType.MOVE_DOWN: ColorProfile(
        block_type=BlockType.MOVE_DOWN,
        lower=(0, 120, 80),
        upper=(10, 255, 255),
        lower2=(170, 120, 80),
        upper2=(180, 255, 255),
    ),
    BlockType.MOVE_LEFT: ColorProfile(
        block_type=BlockType.MOVE_LEFT,
        lower=(20, 100, 100),
        upper=(35, 255, 255),
    ),
    BlockType.MOVE_RIGHT: ColorProfile(
        block_type=BlockType.MOVE_RIGHT,
        lower=(130, 60, 60),
        upper=(160, 255, 255),
    ),
    BlockType.LOOP_START: ColorProfile(
        block_type=BlockType.LOOP_START,
        lower=(10, 150, 150),
        upper=(20, 255, 255),
    ),
    BlockType.LOOP_END: ColorProfile(
        block_type=BlockType.LOOP_END,
        lower=(160, 80, 80),
        upper=(175, 255, 255),
    ),
}
# fmt: on
