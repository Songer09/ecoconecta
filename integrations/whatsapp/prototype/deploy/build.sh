#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python -m pip install -r requirements.txt
npm ci --no-audit --no-fund
npm run build
