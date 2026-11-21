#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# El alojamiento configura HOST=0.0.0.0 detrás de su proxy HTTPS.
exec python -m uvicorn app.main:app \
  --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}" \
  --no-access-log --no-server-header
