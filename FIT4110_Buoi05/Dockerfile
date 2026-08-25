# syntax=docker/dockerfile:1.7
# Multi-stage build for AI Vision Service (Buoi05).
# Source: FIT4110_Buoi03_Postman_Mock_Testing/src/ai_vision_service (only this module is packaged).
# Camera Stream & Core Business mocks are NOT packaged — they run on the host
# at their real LAN IPs and are configured via .env at runtime.

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
ENV APP_PORT=8000
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /app appuser

COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src/

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

CMD ["sh", "-c", "uvicorn ai_vision_service.main:app --host ${APP_HOST} --port ${APP_PORT} --app-dir /app/src"]
