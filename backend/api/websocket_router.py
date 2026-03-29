"""
WebSocket route: ws://host/ws/execute

Her çalıştırma için yeni bağlantı açılır, done sonrası kapanır.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.models import WebSocketMessage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

_STEP_DELAY_S = 0.55


@router.websocket("/ws/execute")
async def execute_program(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("WebSocket bağlandı: %s", websocket.client)

    try:
        raw = await websocket.receive_text()
        payload = json.loads(raw)
        steps = payload.get("steps", [])

        if not steps:
            await _send(websocket, WebSocketMessage(
                event="error", message="Adım listesi boş."
            ))
            return

        await _broadcast_steps(websocket, steps)

    except WebSocketDisconnect:
        logger.info("WebSocket bağlantısı kesildi: %s", websocket.client)
    except json.JSONDecodeError:
        logger.warning("Geçersiz JSON geldi.")
    except Exception as exc:
        logger.exception("WebSocket hatası: %s", exc)


async def _broadcast_steps(websocket: WebSocket, steps: list) -> None:
    total = len(steps)

    await _send(websocket, WebSocketMessage(event="reset"))
    await asyncio.sleep(0.25)

    for idx, step in enumerate(steps):
        action = step.get("action") if isinstance(step, dict) else step
        await _send(websocket, WebSocketMessage(
            event="step",
            step_index=idx,
            action=action,
            total_steps=total,
        ))
        await asyncio.sleep(_STEP_DELAY_S)

    await _send(websocket, WebSocketMessage(event="done", total_steps=total))


async def _send(websocket: WebSocket, msg: WebSocketMessage) -> None:
    await websocket.send_text(msg.model_dump_json())
