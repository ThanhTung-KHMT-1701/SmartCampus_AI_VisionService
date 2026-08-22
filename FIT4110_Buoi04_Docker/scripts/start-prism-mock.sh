#!/usr/bin/env bash
# Start Prism mock for AI Vision (port 4011).
# Usage: scripts/start-prism-mock.sh
#
# This is a thin wrapper around `npx prism mock` so contributors do not have
# to remember the port and host flags. Useful for Lab 03 and for the
# FIT4110_lab04_ai_vision_mock.postman_environment.json.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTRACT="${ROOT}/contracts/ai-vision.openapi.yaml"

if [ ! -f "$CONTRACT" ]; then
    echo "Contract not found: $CONTRACT" >&2
    exit 1
fi

exec npx prism mock "$CONTRACT" --host 0.0.0.0 --port 4011
