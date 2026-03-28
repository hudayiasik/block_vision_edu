"""
Converts an unordered list of detected blocks into reading order.

Reading order for physical block programs:
  • Primarily left → right (same row)
  • Then top → bottom (next row)

Blocks are bucketed into rows using a configurable tolerance
so slight vertical misalignment on the table doesn't break ordering.
"""

from __future__ import annotations

from typing import List

from backend.models import DetectedBlock

_DEFAULT_ROW_TOLERANCE_PX = 60


class BlockSorter:
    """
    Single Responsibility: spatial ordering of blocks only.

    Usage::

        sorter = BlockSorter(row_tolerance=60)
        ordered = sorter.sort(detected_blocks)
    """

    def __init__(self, row_tolerance: int = _DEFAULT_ROW_TOLERANCE_PX) -> None:
        self._row_tolerance = row_tolerance

    def sort(self, blocks: List[DetectedBlock]) -> List[DetectedBlock]:
        """Return blocks in left-to-right, top-to-bottom reading order."""
        if not blocks:
            return []

        rows = self._group_into_rows(blocks)
        ordered: List[DetectedBlock] = []
        for row in rows:
            ordered.extend(sorted(row, key=lambda b: b.bounding_box.center[0]))

        return ordered

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _group_into_rows(
        self, blocks: List[DetectedBlock]
    ) -> List[List[DetectedBlock]]:
        """Cluster blocks by approximate Y center position."""
        sorted_by_y = sorted(blocks, key=lambda b: b.bounding_box.center[1])
        rows: List[List[DetectedBlock]] = []
        current_row: List[DetectedBlock] = []
        current_y: int = sorted_by_y[0].bounding_box.center[1]

        for block in sorted_by_y:
            cy = block.bounding_box.center[1]
            if abs(cy - current_y) <= self._row_tolerance:
                current_row.append(block)
            else:
                rows.append(current_row)
                current_row = [block]
                current_y = cy

        if current_row:
            rows.append(current_row)

        return rows
