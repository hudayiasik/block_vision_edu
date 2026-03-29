"""
Gemini-based block detector.

Birden fazla API key destekler — rate limit (429) gelince
otomatik olarak bir sonraki key'e geçer (round-robin).
API key hiçbir zaman URL veya loglarda görünmez.
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

_SYSTEM_PROMPT = (
    "You are analyzing a photo of physical programming blocks for a kids educational toy.\n\n"
    "READING ORDER: Read blocks like a book — left to right, then next row, top to bottom.\n\n"
    "BLOCK TYPES — identify only by the TEXT or SYMBOL visible on the card:\n"
    "  - start       : play symbol or text START / BASLAT\n"
    "  - move_up     : up arrow AND text YUKARI or UP or Move Up\n"
    "  - move_down   : down arrow AND text ASAGI or DOWN or Move Down\n"
    "  - move_left   : left arrow AND text SOL or LEFT or Move Left\n"
    "  - move_right  : right arrow AND text SAG or RIGHT or Move Right\n"
    "  - loop_start  : repeat symbol or text DONGU / LOOP, with a number on it\n"
    "  - loop_end    : end symbol or text BITIS / END\n\n"
    "CRITICAL RULES:\n"
    "  1. A card MUST have readable text or clear label — do NOT guess from color alone.\n"
    "  2. If a card has an arrow but NO readable label, mark it as unknown.\n"
    "  3. If a card is partially out of frame or unreadable, mark it as unknown.\n"
    "  4. Only count cards that are clearly and fully visible with a readable label.\n"
    "  5. Read row by row, left to right. Report blocks in that exact order.\n\n"
    "Return ONLY a valid JSON array, no markdown, no explanation, no code fences.\n"
    "Each item must have exactly these keys:\n"
    '  "block_type"  : string (start/move_up/move_down/move_left/move_right/loop_start/loop_end/unknown)\n'
    '  "confidence"  : float 0.0-1.0\n'
    '  "loop_count"  : integer if loop_start, else null\n'
    '  "bbox_x"      : left pixel as integer\n'
    '  "bbox_y"      : top pixel as integer\n'
    '  "bbox_w"      : width in pixels as integer\n'
    '  "bbox_h"      : height in pixels as integer\n\n'
    "If no valid labeled blocks found, return: []"
)

_VALID_BLOCK_TYPES = {bt.value for bt in BlockType}


class GeminiBlockDetector(BaseBlockDetector):
    """
    Gemini Vision API ile blok tespiti.
    Birden fazla key verildiyse 429 hatalarında otomatik döner.
    """

    def __init__(self, api_keys: List[str], model: str = "gemini-2.5-flash-lite") -> None:
        if not api_keys:
            raise ValueError("En az bir Gemini API key gerekli.")
        self._keys = api_keys
        self._current_key_idx = 0
        self._model = model
        self._client = httpx.Client(timeout=60.0)
        logger.info(
            "GeminiBlockDetector başlatıldı: %d key, model=%s",
            len(self._keys), self._model
        )

    @property
    def _current_key(self) -> str:
        return self._keys[self._current_key_idx]

    def _rotate_key(self) -> bool:
        """Sonraki key'e geç. Tüm keyler denendiyse False döner."""
        next_idx = (self._current_key_idx + 1) % len(self._keys)
        if next_idx == self._current_key_idx:
            return False  # tek key var, döndürme yok
        self._current_key_idx = next_idx
        logger.info("API key rotasyonu: key %d/%d", self._current_key_idx + 1, len(self._keys))
        return True

    def detect_from_bytes(self, image_bytes: bytes) -> List[DetectedBlock]:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = self._build_payload(b64)
        raw_json = self._call_gemini_with_rotation(payload)
        blocks = self._parse_response(raw_json)
        logger.info("Gemini %d blok tespit etti.", len(blocks))
        return blocks

    def detect(self, image) -> List[DetectedBlock]:  # type: ignore[override]
        import cv2
        ok, buf = cv2.imencode(".jpg", image)
        if not ok:
            raise ValueError("Görüntü JPEG'e dönüştürülemedi.")
        return self.detect_from_bytes(bytes(buf))

    def _build_payload(self, b64_image: str) -> dict:
        return {
            "contents": [
                {
                    "parts": [
                        {"text": _SYSTEM_PROMPT},
                        {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}},
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024},
        }

    def _call_gemini_with_rotation(self, payload: dict) -> str:
        """
        Tüm keyler üzerinden dener:
          - 429 → başka key varsa döndür, yoksa bekle
          - 200 → döndür
          - diğer hata → hemen fırlat
        """
        tried_keys = set()
        wait_seconds = [5, 15, 30]
        wait_idx = 0

        while True:
            tried_keys.add(self._current_key_idx)
            try:
                return self._call_once(payload)
            except _RateLimitError:
                # Başka key var mı?
                rotated = self._rotate_key()
                if rotated and self._current_key_idx not in tried_keys:
                    logger.info("429 — farklı key deneniyor...")
                    continue

                # Tüm keyler denendi, bekle
                if wait_idx < len(wait_seconds):
                    wait = wait_seconds[wait_idx]
                    wait_idx += 1
                    tried_keys.clear()  # tekrar dene
                    logger.warning("Tüm keyler rate limit'te. %ds bekleniyor...", wait)
                    time.sleep(wait)
                else:
                    raise RuntimeError(
                        "Tüm Gemini API keyleri rate limit'e ulaşti. "
                        "1-2 dakika bekleyip tekrar deneyin."
                    )

    def _call_once(self, payload: dict) -> str:
        """Tek bir API isteği yapar. 429'da _RateLimitError fırlatır."""
        url = f"{_GEMINI_BASE_URL}/{self._model}:generateContent"
        headers = {
            "x-goog-api-key": self._current_key,
            "Content-Type": "application/json",
        }
        try:
            response = self._client.post(url, headers=headers, json=payload)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Bağlantı hatası: {type(exc).__name__}") from exc

        if response.status_code == 429:
            raise _RateLimitError()

        if not response.is_success:
            logger.error("Gemini HTTP %d: %s", response.status_code, response.text[:200])
            raise RuntimeError(f"Gemini API HTTP {response.status_code}")

        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Beklenmedik Gemini yanıt formatı.") from exc

    def _parse_response(self, text: str) -> List[DetectedBlock]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(
                l for l in cleaned.splitlines() if not l.startswith("```")
            ).strip()

        try:
            items = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("JSON parse hatasi: %s | Raw: %s", exc, text[:300])
            return []

        if not isinstance(items, list):
            return []

        return [b for item in items if (b := self._item_to_block(item))]

    @staticmethod
    def _item_to_block(item: dict) -> DetectedBlock | None:
        try:
            raw_type = str(item.get("block_type", "unknown")).lower()
            block_type = (
                BlockType(raw_type) if raw_type in _VALID_BLOCK_TYPES else BlockType.UNKNOWN
            )
            loop_count = item.get("loop_count")
            if loop_count is not None:
                loop_count = max(1, min(int(loop_count), 10))

            return DetectedBlock(
                block_type=block_type,
                bounding_box=BoundingBox(
                    x=int(item.get("bbox_x", 0)),
                    y=int(item.get("bbox_y", 0)),
                    width=int(item.get("bbox_w", 80)),
                    height=int(item.get("bbox_h", 80)),
                ),
                confidence=float(item.get("confidence", 0.8)),
                loop_count=loop_count,
            )
        except Exception as exc:
            logger.warning("Hatali blok atlandi: %s — %s", item, exc)
            return None


class _RateLimitError(Exception):
    """Dahili: 429 sinyali için."""
    pass
