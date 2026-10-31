"""Root FastAPI entrypoint for Saytm Voice Assistant.

Enables default entrypoint detection for `fastapi dev`, `fastapi run`,
and IDE preview runners without needing explicit path configuration.
"""
import uvicorn
from backend.app import app

__all__ = ["app"]

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)

