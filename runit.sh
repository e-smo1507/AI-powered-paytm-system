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

exec "$python" -m uvicorn main:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-8000}" \
  ${RELOAD:+--reload}
