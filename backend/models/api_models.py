"""
Pydantic schemas for HTTP request/response bodies.
Kept separate from domain models (SRP).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class StepSchema(BaseModel):
    """One atomic action the cat must perform."""

    action: str = Field(..., description="e.g. 'move_up', 'move_right'")
    repeat: int = Field(default=1, ge=1)


class AnalyzeResponse(BaseModel):
    """Returned after POST /api/analyze-image."""

    success: bool
    steps: List[StepSchema] = Field(default_factory=list)
    raw_blocks: List[str] = Field(default_factory=list, description="Detected block names in order")
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """Real-time message pushed over WS during execution."""

    event: str              # "step" | "done" | "error" | "reset"
    step_index: Optional[int] = None
    action: Optional[str] = None
    total_steps: Optional[int] = None
    message: Optional[str] = None
