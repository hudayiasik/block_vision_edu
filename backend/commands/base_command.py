"""
Command Pattern base class.

Each physical block maps to a Command object that knows
how to serialize itself for the frontend.

Benefits:
  • Each command is independently testable.
  • New block types = new Command subclass, nothing else changes.
  • Commands can be queued, reversed, or replayed (extensibility).
"""

from __future__ import annotations

import abc
from typing import List

from backend.models import StepSchema


class BaseCommand(abc.ABC):
    """
    Every block command must be able to expand itself into
    a flat list of StepSchema that the frontend understands.
    """

    @abc.abstractmethod
    def to_steps(self) -> List[StepSchema]:
        """Expand this command into one or more atomic frontend steps."""
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable name for logging/debugging."""
        ...
