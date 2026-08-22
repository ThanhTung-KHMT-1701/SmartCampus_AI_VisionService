#!/usr/bin/env bash
# Run Newman collection against an environment.
# Usage: scripts/run-newman.sh [local|mock]
#
# This script:
#   1. Verifies the stack is up by curling /health for AI Vision.
#   2. Runs newman against the chosen environment.
#   3. Writes junit + htmlextra reports into reports/.

set -euo pipefail

TARGET="${1:-local}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COLLECTION="${ROOT}/postman/collections/FIT4110_lab04_ai_vision.postman_collection.json"
REPORTS_DIR="${ROOT}/reports"

case "$TARGET" in
    local)
        ENV="${ROOT}/postman/environments/FIT4110_lab04_ai_vision_local.postman_environment.json"
        REPORT_BASE="${REPORTS_DIR}/newman-vision-local"
        HEALTH_URL="http://localhost:8000/health"
        ;;
    mock)
        ENV="${ROOT}/postman/environments/FIT4110_lab04_ai_vision_mock.postman_environment.json"
        REPORT_BASE="${REPORTS_DIR}/newman-vision-mock"
        HEALTH_URL="http://localhost:4011/health"
        ;;
    *)
        echo "Usage: $0 [local|mock]" >&2
        exit 2
        ;;
esac

if [ ! -f "$COLLECTION" ]; then
    echo "Collection not found: $COLLECTION" >&2
    exit 1
fi

if [ ! -f "$ENV" ]; then
    echo "Environment not found: $ENV" >&2
    exit 1
fi

mkdir -p "$REPORTS_DIR"

echo "[1/3] Checking target ${HEALTH_URL} ..."
code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "${HEALTH_URL}" || echo 000)"
if [ "$code" != "200" ]; then
    echo "Target not healthy (got ${code}). For 'local' run: docker compose up -d --build." >&2
    exit 1
fi

echo "[2/3] Running newman (target=${TARGET}) ..."
npx newman run "$COLLECTION" \
    -e "$ENV" \
    -r cli,junit,htmlextra \
    --reporter-junit-export "${REPORT_BASE}.xml" \
    --reporter-htmlextra-export "${REPORT_BASE}.html"

echo "[3/3] Reports written:"
echo "  ${REPORT_BASE}.xml"
echo "  ${REPORT_BASE}.html"
