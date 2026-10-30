#!/usr/bin/env python
"""Run backend tests"""
import subprocess, sys

result = subprocess.run(
    [sys.executable, "-m", "backend.test_journeys"],
    cwd="/c/Users/lenovo/Downloads/paytm-voice-assistant/paytm-voice-assistant",
    capture_output=True, text=True, timeout=60
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RC:", result.returncode)
