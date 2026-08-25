# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS builder

# Không ghi bytecode và hiển thị stdout ngay lập tức
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Tạo virtualenv riêng để giảm layer image
RUN python -m venv /opt/venv

COPY requirements.txt .

RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Biến runtime mặc định – có thể override qua .env
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV AUTH_TOKEN=local-dev-token
ENV SERVICE_NAME=iot-ingestion
ENV SERVICE_VERSION=0.5.0

WORKDIR /app

# Tạo user non‑root để chạy app an toàn
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /app appuser

COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src/

# Cấp quyền cho user
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Healthcheck sử dụng endpoint /health của API
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

# Chạy API bằng uvicorn
CMD ["sh", "-c", "uvicorn iot_app.main:app --app-dir src --host ${APP_HOST} --port ${APP_PORT}"]