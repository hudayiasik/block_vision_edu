"""
Movement command implementations.
One class per direction — open for extension (diagonal, jump, etc.).
"""

from __future__ import annotations

from typing import List

from backend.commands.base_command import BaseCommand
from backend.models import StepSchema


class MoveUpCommand(BaseCommand):
    name = "move_up"

    def to_steps(self) -> List[StepSchema]:
        return [StepSchema(action="move_up")]


class MoveDownCommand(BaseCommand):
    name = "move_down"

    def to_steps(self) -> List[StepSchema]:
        return [StepSchema(action="move_down")]


class MoveLeftCommand(BaseCommand):
    name = "move_left"

    def to_steps(self) -> List[StepSchema]:
        return [StepSchema(action="move_left")]


class MoveRightCommand(BaseCommand):
    name = "move_right"

    def to_steps(self) -> List[StepSchema]:
        return [StepSchema(action="move_right")]
