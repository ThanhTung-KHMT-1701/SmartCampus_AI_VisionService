# syntax=docker/dockerfile:1.7
# Multi-stage build cho AI Vision Service (team-vision, FIT4110 Buổi 05).
# YOLOv8 chạy in-process — không cần container riêng ai-yolo.
# Stage runtime chạy non-root và có HEALTHCHECK gọi /health.

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv

COPY requirements-yolo.txt ./requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Tải pretrained yolov8n.pt (~6 MB) tại build time — bake vào image.
RUN /opt/venv/bin/python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" \
    && ls -la yolov8n.pt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"

ENV APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    PYTHONPATH=/app/src \
    AI_VISION_AUTH_TOKEN=local-dev-token-vision \
    SERVICE_NAME=ai-vision \
    SERVICE_VERSION=0.5.0 \
    VISION_DB_PATH=/data/vision.db \
    YOLO_WEIGHTS_PATH=/app/yolov8n.pt \
    LOG_LEVEL=INFO

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /app appuser

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/yolov8n.pt /app/yolov8n.pt
COPY src/ ./src/

RUN mkdir -p /data && chown -R appuser:appgroup /app /data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["sh", "-c", "uvicorn ai_vision_service.main:app --host ${APP_HOST} --port ${APP_PORT} --app-dir /app/src"]
