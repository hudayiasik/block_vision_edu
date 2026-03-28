"""
WebSocket route: ws://host/ws/execute

Clients (frontend) connect here. When they send a JSON payload
with a list of steps, the server echoes them back one by one
with a configurable delay so the frontend can animate each move.

Flow:
  Client → { "steps": [...] }
  Server → { "event": "step", "step_index": 0, "action": "move_up", "total_steps": 5 }
  Server → { "event": "step", "step_index": 1, ... }
  ...
  Server → { "event": "done" }
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.models import WebSocketMessage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Seconds between each step broadcast (gives frontend time to animate)
_STEP_DELAY_S = 0.6


@router.websocket("/ws/execute")
async def execute_program(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("WebSocket client connected: %s", websocket.client)

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            steps = payload.get("steps", [])

            if not steps:
                await _send(websocket, WebSocketMessage(event="error", message="No steps received."))
                continue

            await _broadcast_steps(websocket, steps)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
        await _send(websocket, WebSocketMessage(event="error", message=str(exc)))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

async def _broadcast_steps(websocket: WebSocket, steps: list) -> None:
    total = len(steps)

    # Notify client to reset the cat position before starting
    await _send(websocket, WebSocketMessage(event="reset"))
    await asyncio.sleep(0.3)

    for idx, step in enumerate(steps):
        action = step.get("action") if isinstance(step, dict) else step
        msg = WebSocketMessage(
            event="step",
            step_index=idx,
            action=action,
            total_steps=total,
        )
        await _send(websocket, msg)
        await asyncio.sleep(_STEP_DELAY_S)

    await _send(websocket, WebSocketMessage(event="done", total_steps=total))


async def _send(websocket: WebSocket, msg: WebSocketMessage) -> None:
    await websocket.send_text(msg.model_dump_json())
