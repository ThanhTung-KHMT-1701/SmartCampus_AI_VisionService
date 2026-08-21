# DOCKER_LAB_GUIDE.md – Hướng dẫn lab Docker

## 1. Vì sao cần Docker?

Vấn đề thường gặp:

```text
Máy em chạy được, máy bạn không chạy được.
```

Docker giải quyết bằng cách đóng gói:

```text
source code + dependency + runtime config + command chạy app
```

thành một image có thể chạy lại ở máy khác.

---

## 2. Image và container

```text
Image     = bản đóng gói bất biến
Container = tiến trình đang chạy từ image
```

Ví dụ:

```bash
docker build -t fit4110/iot-ingestion:lab04 .
docker run -p 8000:8000 fit4110/iot-ingestion:lab04
```

---

## 3. Dockerfile tối thiểu

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
EXPOSE 8000
CMD ["uvicorn", "iot_app.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
```

Dockerfile trong repo này tốt hơn bản tối thiểu vì có:

- multi-stage build
- non-root user
- healthcheck
- environment variables
- `.dockerignore`

---

## 4. Healthcheck

Container không chỉ cần "đang chạy", mà cần "service bên trong sẵn sàng".

```Dockerfile
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1
```

Kiểm tra:

```bash
docker ps
docker inspect fit4110-iot-lab04
```

---

## 5. Không đưa secret vào image

Không viết trực tiếp token vào code hoặc Dockerfile.

Sai:

```Dockerfile
ENV TELEGRAM_TOKEN=123456
```

Đúng:

```Dockerfile
ENV TELEGRAM_TOKEN=
```

và truyền khi chạy:

```bash
docker run --env-file .env ...
```
