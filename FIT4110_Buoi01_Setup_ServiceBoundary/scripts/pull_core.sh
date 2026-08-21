#!/usr/bin/env bash
set -u
IMAGES=(hello-world:latest python:3.11-slim node:20-alpine nginx:alpine redis:7-alpine registry:2)
mkdir -p evidence/buoi-01
LOG=evidence/buoi-01/pull-core-result.txt
: > "$LOG"
for img in "${IMAGES[@]}"; do
  echo "==> Pulling $img" | tee -a "$LOG"
  if docker pull "$img" 2>&1 | tee -a "$LOG"; then
    echo "[PASS] $img" | tee -a "$LOG"
  else
    echo "[WARN] $img" | tee -a "$LOG"
  fi
done
