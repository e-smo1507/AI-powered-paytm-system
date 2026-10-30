#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x .venv/bin/python ]]; then
  python=.venv/bin/python
else
  python="${PYTHON:-python3}"
fi

if ! "$python" -c 'import uvicorn' >/dev/null 2>&1; then
  printf 'Uvicorn is missing. Install dependencies with: %s -m pip install -r requirements.txt\n' "$python" >&2
  exit 1
fi

exec "$python" -m uvicorn backend.app:app \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8000}" \
  --reload
