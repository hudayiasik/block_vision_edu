"""
Loop command using the Composite Pattern.

A LoopCommand wraps a list of child commands and repeats them N times.
This supports nested loops naturally because each child can itself
be a LoopCommand.
"""

from __future__ import annotations

from typing import List

from backend.commands.base_command import BaseCommand
from backend.models import StepSchema


class LoopCommand(BaseCommand):
    """
    Composite Pattern: LoopCommand contains child BaseCommand objects
    and repeats their steps `repeat` times when expanded.

    Example::
        loop = LoopCommand(repeat=3, children=[MoveRightCommand(), MoveDownCommand()])
        loop.to_steps()
        # → [move_right, move_down, move_right, move_down, move_right, move_down]
    """

    def __init__(self, repeat: int, children: List[BaseCommand]) -> None:
        if repeat < 1:
            raise ValueError("repeat must be >= 1")
        self._repeat = repeat
        self._children = children

    @property
    def name(self) -> str:
        return f"loop(x{self._repeat})"

    def to_steps(self) -> List[StepSchema]:
        child_steps: List[StepSchema] = []
        for child in self._children:
            child_steps.extend(child.to_steps())

        return child_steps * self._repeat
