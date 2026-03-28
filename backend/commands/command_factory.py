"""
Factory Pattern: maps BlockType → concrete BaseCommand instance.

Adding a new block type requires only:
  1. A new Command subclass in the commands package.
  2. One entry in _MOVEMENT_MAP below.
  Nothing else changes (Open/Closed Principle).
"""

from __future__ import annotations

from typing import Dict, List, Type

from backend.commands.base_command import BaseCommand
from backend.commands.loop_command import LoopCommand
from backend.commands.movement_commands import (
    MoveDownCommand,
    MoveLeftCommand,
    MoveRightCommand,
    MoveUpCommand,
)
from backend.models import BlockType, DetectedBlock

# Simple movement blocks: BlockType → Command class (no args needed)
_MOVEMENT_MAP: Dict[BlockType, Type[BaseCommand]] = {
    BlockType.MOVE_UP: MoveUpCommand,
    BlockType.MOVE_DOWN: MoveDownCommand,
    BlockType.MOVE_LEFT: MoveLeftCommand,
    BlockType.MOVE_RIGHT: MoveRightCommand,
}


class CommandFactory:
    """
    Transforms a flat, ordered list of DetectedBlock into a
    structured list of BaseCommand objects (with loops resolved).

    Usage::
        factory = CommandFactory()
        commands = factory.build(ordered_blocks)
    """

    def build(self, blocks: List[DetectedBlock]) -> List[BaseCommand]:
        """
        Parse blocks into a command tree.
        Handles nested loops via a stack.
        """
        commands, _ = self._parse(blocks, start_index=0, inside_loop=False)
        return commands

    # ------------------------------------------------------------------
    # Private recursive parser
    # ------------------------------------------------------------------

    def _parse(
        self,
        blocks: List[DetectedBlock],
        start_index: int,
        inside_loop: bool,
    ) -> tuple[List[BaseCommand], int]:
        """
        Returns (commands, next_index_to_consume).
        Recurses when a LOOP_START is encountered.
        """
        commands: List[BaseCommand] = []
        i = start_index

        while i < len(blocks):
            block = blocks[i]

            if block.block_type == BlockType.START:
                i += 1
                continue  # skip START sentinel

            if block.block_type in _MOVEMENT_MAP:
                cmd_class = _MOVEMENT_MAP[block.block_type]
                commands.append(cmd_class())
                i += 1

            elif block.block_type == BlockType.LOOP_START:
                repeat = block.loop_count or 3
                # Recurse to collect the loop body
                children, i = self._parse(blocks, i + 1, inside_loop=True)
                commands.append(LoopCommand(repeat=repeat, children=children))

            elif block.block_type == BlockType.LOOP_END:
                if inside_loop:
                    return commands, i + 1  # hand control back to parent
                i += 1  # stray LOOP_END – skip gracefully

            else:
                i += 1  # UNKNOWN – skip

        return commands, i
