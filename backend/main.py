"""
Backend startup script — programmatic entrypoint for the backend FastAPI app.
"""
from typing import Optional
import os

# Import FastAPI app instance
from backend.api.main import app

import uvicorn


def start(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """
    Programmatically start the FastAPI application.

    Args:
        host: host to bind to (default 0.0.0.0)
        port: port to bind to (default 8000)
        reload: enable auto-reload (development only)
    """
    uvicorn.run(app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    # Respect DEV_RELOAD env var for development convenience
    reload_flag = os.getenv("DEV_RELOAD", "false").lower() == "true"
    start(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")), reload=reload_flag)


