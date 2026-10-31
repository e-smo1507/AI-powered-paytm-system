"""Root FastAPI entrypoint for Saytm Voice Assistant.

Enables default entrypoint detection for `uvicorn app:app`, `fastapi run app.py`,
and standard FastAPI application discovery.
"""
import uvicorn
from backend.app import app

__all__ = ["app"]

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)

