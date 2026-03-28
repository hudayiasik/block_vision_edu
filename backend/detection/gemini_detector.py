"""
Gemini-based block detector.

Strategy Pattern: implements BaseBlockDetector using Google Gemini Vision.
The rest of the pipeline (BlockSorter, CommandFactory) is completely unaware
that detection now happens via an LLM instead of OpenCV.

Security:
    API key is sent via x-goog-api-key header — never in the URL,
    never logged, never included in error messages.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import List

import httpx

from backend.detection.base_detector import BaseBlockDetector
from backend.models import BlockType, BoundingBox, DetectedBlock

logger = logging.getLogger(__name__)

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

_SYSTEM_PROMPT = """
You are analyzing a photo of physical programming blocks for a kids' educational toy.

READING ORDER: Read blocks exactly like a book — left to right, then move to the next row, top to bottom. Never skip a row or read vertically.

YOUR TASK: Look at each card and identify what instruction is written or drawn on it.

BLOCK TYPES — identify by the TEXT or SYMBOL visible on the card face:
  - start       : shows a play symbol (▶) or the word START / BAŞLAT
  - move_up     : shows an UP arrow (↑) AND the word YUKARI or UP or Move Up
  - move_down   : shows a DOWN arrow (↓) AND the word AŞAĞI or DOWN or Move Down  
  - move_left   : shows a LEFT arrow (←) AND the word SOL or LEFT or Move Left
  - move_right  : shows a RIGHT arrow (→) AND the word SAĞ or RIGHT or Move Right
  - loop_start  : shows a repeat/loop symbol (🔁) or the word DÖNGÜ / LOOP, with a number
  - loop_end    : shows an end symbol or the word BİTİŞ / END

CRITICAL RULES:
  1. A card MUST have readable text or a clear label to be identified — do NOT guess from color alone.
  2. If a card has an arrow but NO readable label/text, mark it as "unknown".
  3. If a card is partially out of frame or unreadable, mark it as "unknown".
  4. Only count cards that are clearly and fully visible with a readable label.
  5. Read row by row, left to right. Report blocks in that exact order.

Return ONLY a valid JSON array, no markdown, no explanation.
Each item must have:
  "block_type"  : string (one of the types above, or "unknown")
  "confidence"  : float 0.0-1.0
  "loop_count"  : integer if loop_start, else null
  "bbox_x"      : left pixel (integer)
  "bbox_y"      : top pixel (integer)  
  "bbox_w"      : width in pixels (integer)
  "bbox_h"      : height in pixels (integer)

If no valid labeled blocks are found, return: []
""".strip()

_VALID_BLOCK_TYPES = {bt.value for bt in BlockType}


class GeminiBlockDetector(BaseBlockDetector):
    """
    Sends the image to Gemini Vision and parses the JSON response
    into DetectedBlock objects.

    API key is sent via x-goog-api-key header — never appears in URLs or logs.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite") -> None:
        if not api_key:
            raise ValueError("Gemini API key must not be empty.")
        self._api_key = api_key
        self._model = model
        self._client = httpx.Client(timeout=60.0)

    # ── BaseBlockDetector contract ────────────────────────────────────────────

    def detect_from_bytes(self, image_bytes: bytes) -> List[DetectedBlock]:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = self._build_payload(b64)
        raw_json = self._call_gemini(payload)
        blocks = self._parse_response(raw_json)
        logger.info("Gemini detected %d block(s).", len(blocks))
        return blocks

    def detect(self, image) -> List[DetectedBlock]:  # type: ignore[override]
        import cv2
        ok, buf = cv2.imencode(".jpg", image)
        if not ok:
            raise ValueError("Could not encode image to JPEG.")
        return self.detect_from_bytes(bytes(buf))

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_payload(self, b64_image: str) -> dict:
        return {
            "contents": [
                {
                    "parts": [
                        {"text": _SYSTEM_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024,
            },
        }

    def _call_gemini(self, payload: dict) -> str:
        """
        Call Gemini API with retry on rate limit (429).
        API key is sent via header — never appears in the URL or logs.
        """
        url = f"{_GEMINI_BASE_URL}/{self._model}:generateContent"
        headers = {
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
        }

        wait_seconds = [5, 15, 30]
        last_error: Exception | None = None

        for attempt, wait in enumerate(wait_seconds):
            try:
                response = self._client.post(url, headers=headers, json=payload)

                if response.status_code == 429:
                    logger.warning(
                        "Gemini rate limit (429). Deneme %d/%d — %ds bekleniyor...",
                        attempt + 1, len(wait_seconds), wait,
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                last_error = RuntimeError(f"Gemini API returned HTTP {status}.")
                break
            except httpx.RequestError as exc:
                last_error = RuntimeError(f"Gemini request failed: {type(exc).__name__}")
                break

            data = response.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as exc:
                last_error = RuntimeError("Unexpected Gemini response structure.")
                break

        if last_error:
            raise last_error

        raise RuntimeError(
            "Gemini rate limit aşıldı (429). "
            "Lütfen 1-2 dakika bekleyip tekrar deneyin."
        )

    def _parse_response(self, text: str) -> List[DetectedBlock]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(
                line for line in cleaned.splitlines()
                if not line.startswith("```")
            ).strip()

        try:
            items = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Gemini JSON parse hatası: %s\nRaw: %s", exc, text[:200])
            return []

        if not isinstance(items, list):
            logger.error("Gemini yanıtı JSON array değil.")
            return []

        return [b for item in items if (b := self._item_to_block(item))]

    @staticmethod
    def _item_to_block(item: dict) -> DetectedBlock | None:
        try:
            raw_type = str(item.get("block_type", "unknown")).lower()
            block_type = (
                BlockType(raw_type)
                if raw_type in _VALID_BLOCK_TYPES
                else BlockType.UNKNOWN
            )
            confidence = float(item.get("confidence", 0.8))
            loop_count = item.get("loop_count")
            if loop_count is not None:
                loop_count = max(1, min(int(loop_count), 10))

            bbox = BoundingBox(
                x=int(item.get("bbox_x", 0)),
                y=int(item.get("bbox_y", 0)),
                width=int(item.get("bbox_w", 80)),
                height=int(item.get("bbox_h", 80)),
            )
            return DetectedBlock(
                block_type=block_type,
                bounding_box=bbox,
                confidence=confidence,
                loop_count=loop_count,
            )
        except Exception as exc:
            logger.warning("Hatalı blok atlandı: %s — %s", item, exc)
            return None
