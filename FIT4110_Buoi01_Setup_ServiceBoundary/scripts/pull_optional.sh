#!/usr/bin/env bash
set -u
IMAGES=(postgres:15-alpine rabbitmq:3-management eclipse-mosquitto:2 traefik:v3.1 swaggerapi/swagger-ui:v5.17.14 prom/prometheus:v2.54.1 grafana/grafana:11.2.0 ultralytics/ultralytics:latest-cpu)
mkdir -p evidence/buoi-01
LOG=evidence/buoi-01/pull-optional-result.txt
: > "$LOG"
for img in "${IMAGES[@]}"; do
  echo "==> Pulling $img" | tee -a "$LOG"
  docker pull "$img" 2>&1 | tee -a "$LOG" || echo "[WARN] $img" | tee -a "$LOG"
done
