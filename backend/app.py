"""
FastAPI application factory.

Keeping app creation in a dedicated module (not main.py) makes
the app importable for testing without side effects.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import image_router, websocket_router
from backend.config import get_settings

logger = logging.getLogger(__name__)

_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("🚀  %s starting up (debug=%s)", settings.app_name, settings.debug)
    yield
    logger.info("🛑  %s shutting down.", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "BlockVision Edu — photograph physical code blocks, "
            "watch the Scratch cat bring them to life."
        ),
        lifespan=_lifespan,
        debug=settings.debug,
    )

    # ── CORS ────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────────────
    app.include_router(image_router)
    app.include_router(websocket_router)

    # ── Serve React/HTML frontend ────────────────────────────────────
    if _FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")

    return app
