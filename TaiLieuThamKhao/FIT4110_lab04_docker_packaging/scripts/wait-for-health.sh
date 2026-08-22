#!/usr/bin/env bash
set -euo pipefail

URL="${1:-http://localhost:8000/health}"
TIMEOUT_SECONDS="${2:-30}"

echo "Waiting for $URL ..."

for i in $(seq 1 "$TIMEOUT_SECONDS"); do
  if curl -fsS "$URL" >/dev/null 2>&1; then
    echo "Service is ready."
    exit 0
  fi
  sleep 1
done

echo "Service did not become ready after ${TIMEOUT_SECONDS}s"
exit 1
