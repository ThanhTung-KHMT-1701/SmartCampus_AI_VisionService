#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-iot}"

case "${MODE}" in
  iot)
    npx prism mock contracts/iot-ingestion.openapi.yaml -p 4010 --host 0.0.0.0
    ;;
  vision)
    npx prism mock contracts/ai-vision.openapi.yaml -p 4011 --host 0.0.0.0
    ;;
  all)
    npm run mock:iot &
    IOT_PID=$!
    npm run mock:vision &
    VISION_PID=$!
    trap 'kill ${IOT_PID} ${VISION_PID} 2>/dev/null || true' EXIT
    wait
    ;;
  *)
    echo "Usage: scripts/start-prism-mock.sh [iot|vision|all]"
    exit 1
    ;;
esac
