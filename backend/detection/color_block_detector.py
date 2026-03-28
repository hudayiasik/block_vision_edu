"""
Color-based block detector using OpenCV HSV thresholding.

Algorithm per block type:
  1. Convert image to HSV color space
  2. Apply the color profile mask (+ morphological cleanup)
  3. Find contours → filter by area / aspect ratio
  4. Each surviving contour = one detected block
  5. For LOOP_START blocks, run OCR (pytesseract) to read repeat count
"""

from __future__ import annotations

import logging
from typing import List, Optional

import cv2
import numpy as np

from backend.detection.base_detector import BaseBlockDetector
from backend.detection.color_config import COLOR_PROFILES, ColorProfile
from backend.models import BlockType, BoundingBox, DetectedBlock

logger = logging.getLogger(__name__)

# Minimum contour area to consider a block (ignore noise)
_MIN_AREA_PX = 1_500
# Blocks are roughly square; allow some tolerance
_MIN_ASPECT = 0.40
_MAX_ASPECT = 2.50
# Morphological kernel size
_MORPH_K = 5


class ColorBlockDetector(BaseBlockDetector):
    """
    Detects physical code blocks by their dominant color.

    Open/Closed: extend COLOR_PROFILES in color_config.py to support
    new block types without modifying this class.
    """

    def __init__(self, min_area: int = _MIN_AREA_PX) -> None:
        self._min_area = min_area
        self._kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (_MORPH_K, _MORPH_K)
        )

    # ------------------------------------------------------------------
    # Public interface (BaseBlockDetector contract)
    # ------------------------------------------------------------------

    def detect(self, image: np.ndarray) -> List[DetectedBlock]:
        """Detect all code blocks in a BGR image."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        blocks: List[DetectedBlock] = []

        for block_type, profile in COLOR_PROFILES.items():
            detections = self._detect_for_profile(hsv, image, block_type, profile)
            blocks.extend(detections)

        logger.info("Detected %d block(s) total.", len(blocks))
        return blocks

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_for_profile(
        self,
        hsv: np.ndarray,
        original_bgr: np.ndarray,
        block_type: BlockType,
        profile: ColorProfile,
    ) -> List[DetectedBlock]:
        mask = self._build_mask(hsv, profile)
        contours = self._find_valid_contours(mask)

        results: List[DetectedBlock] = []
        for contour in contours:
            bbox = self._contour_to_bbox(contour)
            loop_count = None
            if block_type == BlockType.LOOP_START:
                loop_count = self._read_loop_count(original_bgr, bbox)

            block = DetectedBlock(
                block_type=block_type,
                bounding_box=bbox,
                confidence=self._estimate_confidence(mask, contour),
                loop_count=loop_count,
            )
            results.append(block)

        return results

    def _build_mask(self, hsv: np.ndarray, profile: ColorProfile) -> np.ndarray:
        """Create a binary mask for the given color profile."""
        mask = cv2.inRange(
            hsv,
            np.array(profile.lower),
            np.array(profile.upper),
        )
        # Handle hues that wrap around (e.g. red)
        if profile.lower2 is not None and profile.upper2 is not None:
            mask2 = cv2.inRange(
                hsv,
                np.array(profile.lower2),
                np.array(profile.upper2),
            )
            mask = cv2.bitwise_or(mask, mask2)

        # Morphological open (remove noise) then close (fill gaps)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._kernel, iterations=2)
        return mask

    def _find_valid_contours(self, mask: np.ndarray) -> List[np.ndarray]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self._min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            aspect = w / h if h > 0 else 0
            if _MIN_ASPECT <= aspect <= _MAX_ASPECT:
                valid.append(cnt)
        return valid

    @staticmethod
    def _contour_to_bbox(contour: np.ndarray) -> BoundingBox:
        x, y, w, h = cv2.boundingRect(contour)
        return BoundingBox(x=x, y=y, width=w, height=h)

    @staticmethod
    def _estimate_confidence(mask: np.ndarray, contour: np.ndarray) -> float:
        """
        Confidence = ratio of contour pixels that are white in the mask.
        A perfect solid color block scores close to 1.0.
        """
        x, y, w, h = cv2.boundingRect(contour)
        roi = mask[y : y + h, x : x + w]
        white_px = int(np.count_nonzero(roi))
        total_px = w * h
        return round(white_px / total_px, 3) if total_px > 0 else 0.0

    @staticmethod
    def _read_loop_count(image_bgr: np.ndarray, bbox: BoundingBox) -> Optional[int]:
        """
        Try to read a digit printed on the LOOP_START block via OCR.
        Falls back to 3 if pytesseract is not installed or unreadable.
        """
        try:
            import pytesseract  # optional dependency

            roi = image_bgr[
                bbox.y : bbox.y + bbox.height,
                bbox.x : bbox.x + bbox.width,
            ]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
            text = pytesseract.image_to_string(
                thresh, config="--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789"
            ).strip()
            if text.isdigit():
                count = int(text)
                return max(1, min(count, 10))  # clamp to [1, 10]
        except Exception:
            pass  # OCR failed – fall back silently
        return 3  # sensible default for kids
