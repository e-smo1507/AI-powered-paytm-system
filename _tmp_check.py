import os, subprocess, sys, re, json

queries = [
    ("toLocaleString", "frontend/index.html"),
    ("Saypatm", "frontend/index.html"),
    ("Saypatm", "frontend/agent.html"),
]

for pattern, path in queries:
    try:
        with open(path, 'r', encoding='utf-8', errors='surrogateescape') as f:
            data = f.read()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        continue
    for i, line in enumerate(data.split('\n')):
        if pattern in line:
            print(f"{path}:{i+1}:{line}")
