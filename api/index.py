"""Vercel serverless entrypoint for Saytm Voice Assistant."""
import os
import sys
from pathlib import Path

# Add root directory to sys.path so backend module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app import app

