"""
Unit tests for GeminiBlockDetector — no real API calls made.
Uses unittest.mock to patch httpx so tests run offline and free.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.detection.gemini_detector import GeminiBlockDetector
from backend.models import BlockType


def _make_detector() -> GeminiBlockDetector:
    return GeminiBlockDetector(api_key="test-key-fake", model="gemini-1.5-flash")


def _mock_response(blocks: list) -> MagicMock:
    """Build a fake httpx response that returns the given block list."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(blocks)}]
                }
            }
        ]
    }
    return mock_resp


class TestGeminiBlockDetector:

    def _call(self, blocks: list) -> list:
        detector = _make_detector()
        with patch.object(detector._client, "post", return_value=_mock_response(blocks)):
            return detector.detect_from_bytes(b"fake_image_bytes")

    def test_parses_simple_sequence(self):
        result = self._call([
            {"block_type": "start",      "confidence": 0.99, "loop_count": None, "bbox_x": 0,   "bbox_y": 0, "bbox_w": 80, "bbox_h": 80},
            {"block_type": "move_up",    "confidence": 0.95, "loop_count": None, "bbox_x": 100, "bbox_y": 0, "bbox_w": 80, "bbox_h": 80},
            {"block_type": "move_right", "confidence": 0.93, "loop_count": None, "bbox_x": 200, "bbox_y": 0, "bbox_w": 80, "bbox_h": 80},
        ])
        types = [b.block_type for b in result]
        assert types == [BlockType.START, BlockType.MOVE_UP, BlockType.MOVE_RIGHT]

    def test_parses_loop_count(self):
        result = self._call([
            {"block_type": "loop_start", "confidence": 0.9, "loop_count": 4, "bbox_x": 0, "bbox_y": 0, "bbox_w": 80, "bbox_h": 80},
        ])
        assert result[0].loop_count == 4

    def test_unknown_type_becomes_unknown(self):
        result = self._call([
            {"block_type": "fly", "confidence": 0.5, "loop_count": None, "bbox_x": 0, "bbox_y": 0, "bbox_w": 80, "bbox_h": 80},
        ])
        assert result[0].block_type == BlockType.UNKNOWN

    def test_empty_response_returns_empty_list(self):
        result = self._call([])
        assert result == []

    def test_malformed_item_is_skipped(self):
        result = self._call([
            {"block_type": "move_up", "confidence": 0.9, "loop_count": None, "bbox_x": 0, "bbox_y": 0, "bbox_w": 80, "bbox_h": 80},
            {"this_is": "garbage"},
        ])
        assert len(result) == 1

    def test_markdown_fences_are_stripped(self):
        detector = _make_detector()
        fenced = "```json\n[{\"block_type\":\"start\",\"confidence\":0.9,\"loop_count\":null,\"bbox_x\":0,\"bbox_y\":0,\"bbox_w\":80,\"bbox_h\":80}]\n```"
        result = detector._parse_response(fenced)
        assert result[0].block_type == BlockType.START

    def test_raises_without_api_key(self):
        with pytest.raises(ValueError, match="API key"):
            GeminiBlockDetector(api_key="")
