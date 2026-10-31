"""Root FastAPI entrypoint for Saytm Voice Assistant.

Enables default entrypoint detection for `fastapi dev`, `fastapi run`,
Docker, Render, Railway, Heroku, and IDE preview runners.
"""
import os
import uvicorn
from backend.app import app

__all__ = ["app"]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "false").lower() in ("true", "1")
    uvicorn.run("backend.app:app", host=host, port=port, reload=reload)
