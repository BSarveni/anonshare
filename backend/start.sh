#!/bin/bash
set -e

PORT="${PORT:-8000}"
echo "=== AnonShare API starting on port ${PORT} (set Railway networking target port to this value) ==="

bash prestart.sh

exec uvicorn main:app --host 0.0.0.0 --port "${PORT}"
