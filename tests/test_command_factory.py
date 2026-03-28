"""Tests for CommandFactory — no CV or network dependency."""

import pytest
from backend.commands.command_factory import CommandFactory
from backend.models import BlockType, BoundingBox, DetectedBlock


def _block(block_type: BlockType, loop_count: int | None = None) -> DetectedBlock:
    return DetectedBlock(
        block_type=block_type,
        bounding_box=BoundingBox(x=0, y=0, width=60, height=60),
        confidence=1.0,
        loop_count=loop_count,
    )


class TestCommandFactory:
    def setup_method(self):
        self.factory = CommandFactory()

    def _steps(self, blocks):
        cmds = self.factory.build(blocks)
        return [s.action for cmd in cmds for s in cmd.to_steps()]

    def test_simple_sequence(self):
        blocks = [
            _block(BlockType.START),
            _block(BlockType.MOVE_UP),
            _block(BlockType.MOVE_RIGHT),
        ]
        assert self._steps(blocks) == ["move_up", "move_right"]

    def test_loop_repeats_body(self):
        blocks = [
            _block(BlockType.START),
            _block(BlockType.LOOP_START, loop_count=3),
            _block(BlockType.MOVE_RIGHT),
            _block(BlockType.LOOP_END),
        ]
        assert self._steps(blocks) == ["move_right"] * 3

    def test_loop_with_multiple_body_steps(self):
        blocks = [
            _block(BlockType.START),
            _block(BlockType.LOOP_START, loop_count=2),
            _block(BlockType.MOVE_UP),
            _block(BlockType.MOVE_DOWN),
            _block(BlockType.LOOP_END),
        ]
        assert self._steps(blocks) == ["move_up", "move_down", "move_up", "move_down"]

    def test_commands_before_and_after_loop(self):
        blocks = [
            _block(BlockType.MOVE_LEFT),
            _block(BlockType.LOOP_START, loop_count=2),
            _block(BlockType.MOVE_UP),
            _block(BlockType.LOOP_END),
            _block(BlockType.MOVE_RIGHT),
        ]
        assert self._steps(blocks) == ["move_left", "move_up", "move_up", "move_right"]

    def test_stray_loop_end_is_ignored(self):
        blocks = [_block(BlockType.MOVE_UP), _block(BlockType.LOOP_END)]
        assert self._steps(blocks) == ["move_up"]

    def test_unknown_blocks_are_skipped(self):
        blocks = [_block(BlockType.UNKNOWN), _block(BlockType.MOVE_DOWN)]
        assert self._steps(blocks) == ["move_down"]

    def test_empty_program(self):
        assert self._steps([]) == []
