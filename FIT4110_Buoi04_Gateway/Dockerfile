# syntax=docker/dockerfile:1.7
# Multi-stage build for Smart Campus API Gateway.
# Forward-proxy 3 internal services; only this image exposes port 8080.

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN python -m venv /opt/venv

COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8080
ENV PYTHONPATH=/app/src

# Default upstream URLs (override via compose env if needed).
ENV AI_VISION_BASE_URL=http://ai-vision:8000
ENV CORE_BUSINESS_BASE_URL=http://core-business-mock:4012
ENV CAMERA_STREAM_BASE_URL=http://camera-stream-mock:4014

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /app appuser

COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src/

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3).read()" || exit 1

CMD ["sh", "-c", "uvicorn gateway.main:app --host ${APP_HOST} --port ${APP_PORT} --app-dir /app/src"]
