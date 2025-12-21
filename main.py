"""
Repository root entrypoint — delegate to backend.start to preserve existing behavior.
"""
from backend.main import start
import os


if __name__ == "__main__":
    # Preserve existing DEV_RELOAD behavior for development
    reload_flag = os.getenv("DEV_RELOAD", "false").lower() == "true"
    start(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")), reload=reload_flag)
