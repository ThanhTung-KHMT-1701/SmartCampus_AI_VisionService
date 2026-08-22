#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-local}"

if [[ "$ENV_NAME" == "mock" ]]; then
  npm run test:mock
elif [[ "$ENV_NAME" == "local" || "$ENV_NAME" == "docker" ]]; then
  npm run test:local
else
  echo "Usage: bash scripts/run-newman.sh [mock|local|docker]"
  exit 1
fi
