"""
Abstract base for all block detectors.

Strategy Pattern: swap ColorBlockDetector for an ML-based detector
without touching any other layer.
"""

from __future__ import annotations

import abc
from typing import List

import numpy as np

from backend.models import DetectedBlock


class BaseBlockDetector(abc.ABC):
    """
    Contract every detector must fulfill.
    Implementations must be stateless so they are thread-safe.
    """

    @abc.abstractmethod
    def detect(self, image: np.ndarray) -> List[DetectedBlock]:
        """
        Detect all blocks in *image* (BGR numpy array).

        Returns a list of DetectedBlock in no particular order.
        Ordering is the responsibility of BlockSorter.
        """
        ...

    def detect_from_bytes(self, image_bytes: bytes) -> List[DetectedBlock]:
        """Convenience wrapper that decodes JPEG/PNG bytes first."""
        import cv2

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image bytes.")
        return self.detect(image)
