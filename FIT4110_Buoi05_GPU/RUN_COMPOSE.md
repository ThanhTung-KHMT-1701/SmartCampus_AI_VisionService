# RUN_COMPOSE.md – Hướng dẫn chạy Lab 05: AI Vision + Docker Compose

---

## 1. Yêu cầu

- Docker Desktop (hoặc Docker Engine) hỗ trợ Compose v2
- Node.js 20.x LTS (tuỳ chọn – chỉ cần nếu chạy Newman test)
- PowerShell hoặc Git Bash

Kiểm tra:

```bash
docker compose version
docker --version
```

---

## 2. Chuẩn bị môi trường

```bash
# Clone repo (hoặc cd vào thư mục)
cd FIT4110_Buoi05_GPU

# Copy .env.example → .env (lần đầu)
# File .env chứa cấu hình không đẩy lên git
cp .env.example .env

# Cài dependencies cho Newman/Spectral (tuỳ chọn)
npm install
```

---

## 3. Chạy stack Docker Compose

### Lệnh cơ bản (3 bước)

```bash
# Bước 1: Build image mới hoặc khi có bản mới
docker compose build

# Bước 2: Khởi động các container
docker compose up -d

# Bước 3: Kiểm tra trạng thái
docker compose ps
```

### Theo dõi log (tuỳ chọn)

```bash
docker compose logs -f
```

### Dừng stack

```bash
docker compose down
```

### Kiểm tra health nhanh

```bash
curl http://localhost:8000/health
curl http://localhost:9000/health
```

---

## 4. Kiểm tra chi tiết từng service

### AI Vision API (port 8000)

```bash
curl http://localhost:8000/health
```

Response mẫu:
```json
{
  "status": "ok",
  "service": "ai-vision",
  "version": "1.0.0",
  "modelLoaded": true,
  "modelVersion": "yolov8n-v1.0"
}
```

### AI inference service (port 9000)

```bash
curl http://localhost:9000/health
```

---

## 5. Chạy Newman test trên stack (tuỳ chọn)

```bash
# Đảm bảo stack đang chạy và health OK
# Sau đó chạy Newman:
npm run test:compose
```

Report sinh tại:
- `reports/newman-lab05-compose.xml`
- `reports/newman-lab05-compose.html`

---

## 6. Dùng Makefile cho các lệnh nhanh

```bash
# Build & chạy
make compose-build
make compose-up

# Kiểm tra trạng thái
make compose-ps

# Theo dõi log
make compose-logs

# Kiểm tra health tất cả service
make compose-health

# Chạy Newman test
make test

# Dừng stack
make compose-down
```

---

## 7. Dừng và dọn dẹp

```bash
# Dừng container
docker compose down
```

---

## 8. Mẹo gỡ lỗi

| Vấn đề | Cách kiểm tra |
|---|---|
| API không start được | `docker compose logs api` – kiểm tra token mismatch |
| AI service trả lỗi 502 | `docker compose logs ai-service` – kiểm tra port 9000 |
| Newman test fail | Chạy `curl http://localhost:8000/health` trước để xác nhận API đã up |

Kiểm tra logs từng service:

```bash
docker compose logs -f ai-vision
docker compose logs -f ai-service
docker compose logs -f core-business-mock
docker compose logs -f camera-stream-mock
```

Kiểm tra network:

```bash
docker network ls
docker network inspect fit4110_buoi05_gpu_team-internal
```

---

## 9. Cấu trúc container trong stack

```
┌──────────────────────────────────────────────────────────────┐
│  team-internal network                                        │
│                                                              │
│  ┌──────────────────────┐  ┌─────────────────────────────┐  │
│  │ fit4110-ai-vision   │  │ fit4110-ai-lab05            │  │
│  │ lab05 (port 8000)   │  │ ai-service (port 9000)      │  │
│  │ AI Vision FastAPI   │──│ YOLO mock inference         │  │
│  └──────────┬─────────┘  └─────────────────────────────┘  │
│              │                                                 │
│  ┌──────────┴──────────┐                                    │
│  │ fit4110-core-mock    │  fit4110-camera-mock              │
│  │ lab05 (port 4012)    │  lab05 (port 4014)                │
│  │ Core Business mock   │  Camera Stream mock                │
│  └─────────────────────┘  └─────────────────────────────────┘
└──────────────────────────────────────────────────────────────┘
                           │
               localhost:8000 ← AI Vision API (dev local)
```

**Mạng `class-net` (external)** chỉ cần khai báo lại khi chạy trên môi trường của giảng viên (plug-a-thon). Ở dev local, chỉ dùng `team-internal`.

**Lưu ý:** AI Vision service dùng `DetectionStore` in-memory, không kết nối database.
