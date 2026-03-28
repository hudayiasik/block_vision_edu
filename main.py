"""
Entry point.

Run with:
    python main.py
or:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
import uvicorn
from backend.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
