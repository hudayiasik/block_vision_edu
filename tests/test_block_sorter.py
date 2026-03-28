"""Tests for BlockSorter — no CV dependency needed."""

import pytest
from backend.detection.block_sorter import BlockSorter
from backend.models import BlockType, BoundingBox, DetectedBlock


def _make_block(block_type: BlockType, x: int, y: int) -> DetectedBlock:
    return DetectedBlock(
        block_type=block_type,
        bounding_box=BoundingBox(x=x, y=y, width=60, height=60),
        confidence=0.9,
    )


class TestBlockSorter:
    def setup_method(self):
        self.sorter = BlockSorter(row_tolerance=60)

    def test_single_row_sorted_left_to_right(self):
        blocks = [
            _make_block(BlockType.MOVE_RIGHT, x=200, y=50),
            _make_block(BlockType.MOVE_UP, x=50, y=50),
            _make_block(BlockType.MOVE_DOWN, x=120, y=50),
        ]
        result = self.sorter.sort(blocks)
        assert [b.block_type for b in result] == [
            BlockType.MOVE_UP,
            BlockType.MOVE_DOWN,
            BlockType.MOVE_RIGHT,
        ]

    def test_two_rows_top_before_bottom(self):
        blocks = [
            _make_block(BlockType.MOVE_DOWN, x=50, y=200),   # row 2
            _make_block(BlockType.MOVE_UP, x=50, y=30),      # row 1
        ]
        result = self.sorter.sort(blocks)
        assert result[0].block_type == BlockType.MOVE_UP
        assert result[1].block_type == BlockType.MOVE_DOWN

    def test_empty_list_returns_empty(self):
        assert self.sorter.sort([]) == []

    def test_blocks_within_tolerance_treated_as_same_row(self):
        # y=50 and y=100 are 50 px apart — within default tolerance of 60
        blocks = [
            _make_block(BlockType.MOVE_RIGHT, x=200, y=100),
            _make_block(BlockType.MOVE_UP, x=50, y=50),
        ]
        result = self.sorter.sort(blocks)
        # same row → sorted by X
        assert result[0].block_type == BlockType.MOVE_UP
        assert result[1].block_type == BlockType.MOVE_RIGHT
