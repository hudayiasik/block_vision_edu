"""
ProgramService: application-layer orchestrator (Facade Pattern).

Coordinates:
  1. BlockDetector  – finds blocks in image
  2. BlockSorter    – orders them spatially
  3. CommandFactory – builds command tree
  4. Expands tree   – flat StepSchema list for the frontend

This is the only class the API layer talks to (Dependency Inversion:
routes depend on the abstraction, not concrete detectors).
"""

from __future__ import annotations

import logging
from typing import List

from backend.commands import CommandFactory
from backend.detection import BaseBlockDetector, BlockSorter
from backend.models import AnalyzeResponse, StepSchema

logger = logging.getLogger(__name__)


class ProgramService:
    """
    Inject any BaseBlockDetector implementation — production color
    detector, an ML model, or a mock for testing.
    """

    def __init__(
        self,
        detector: BaseBlockDetector,
        sorter: BlockSorter | None = None,
        factory: CommandFactory | None = None,
    ) -> None:
        self._detector = detector
        self._sorter = sorter or BlockSorter()
        self._factory = factory or CommandFactory()

    def analyze_image(self, image_bytes: bytes) -> AnalyzeResponse:
        """
        Full pipeline: bytes → AnalyzeResponse with flat step list.
        """
        try:
            raw_blocks = self._detector.detect_from_bytes(image_bytes)
        except Exception as exc:
            logger.exception("Detection failed.")
            return AnalyzeResponse(success=False, error=str(exc))

        if not raw_blocks:
            logger.warning("No blocks detected in image.")
            return AnalyzeResponse(
                success=True,
                steps=[],
                raw_blocks=[],
                error="No blocks detected. Try better lighting or place blocks flat.",
            )

        ordered = self._sorter.sort(raw_blocks)
        raw_names = [b.block_type.value for b in ordered]
        logger.info("Block sequence: %s", raw_names)

        commands = self._factory.build(ordered)
        steps: List[StepSchema] = []
        for cmd in commands:
            steps.extend(cmd.to_steps())

        logger.info("Compiled to %d step(s).", len(steps))
        return AnalyzeResponse(success=True, steps=steps, raw_blocks=raw_names)
