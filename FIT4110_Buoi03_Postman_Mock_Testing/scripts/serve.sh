#!/usr/bin/env bash
# Run AI Vision service or side mocks.
# Usage: ./scripts/serve.sh <service>
#   service = vision | camera-mock | core-mock
set -euo pipefail

SERVICE="${1:-vision}"

case "$SERVICE" in
  vision)
    APP="ai_vision_service.main:app"
    PORT=8000
    ;;
  camera-mock)
    APP="side_mocks.camera_stream:app"
    PORT=4014
    ;;
  core-mock)
    APP="side_mocks.core_business:app"
    PORT=4012
    ;;
  *)
    echo "Unknown service: $SERVICE" >&2
    exit 1
    ;;
esac

export PYTHONPATH="${PYTHONPATH:-src}"
exec python -m uvicorn "$APP" --host 127.0.0.1 --port "$PORT" --log-level warning
