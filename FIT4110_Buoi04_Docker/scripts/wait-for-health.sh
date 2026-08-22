#!/usr/bin/env bash
# Wait until a container's /health returns 200, or fail after a timeout.
# Usage: scripts/wait-for-health.sh <hostname> <port> [timeout_seconds]

set -euo pipefail

HOST="${1:-localhost}"
PORT="${2:-8000}"
TIMEOUT="${3:-60}"
URL="http://${HOST}:${PORT}/health"

echo "Waiting for ${URL} (timeout ${TIMEOUT}s) ..."

deadline=$((SECONDS + TIMEOUT))
while [ $SECONDS -lt $deadline ]; do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "${URL}" || echo 000)"
    if [ "$code" = "200" ]; then
        echo "OK: ${URL} returned 200"
        exit 0
    fi
    sleep 2
done

echo "TIMEOUT: ${URL} never returned 200 within ${TIMEOUT}s" >&2
exit 1
