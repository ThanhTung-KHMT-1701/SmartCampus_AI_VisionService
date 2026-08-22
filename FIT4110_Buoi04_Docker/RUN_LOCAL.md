# RUN_LOCAL.md – Hướng dẫn chạy Lab 04 (team-vision)

Tài liệu này hướng dẫn người khác clone repo sạch và chạy lại toàn bộ stack trong Docker.

---

## 1. Yêu cầu môi trường

- Git
- Docker Desktop hoặc Docker Engine (Compose v2)
- Node.js 20.x LTS + npm

Kiểm tra nhanh:

```bash
docker --version
docker compose version
node --version
```

---

## 2. Clone repo và cài dependency

```bash
git clone <repo-url>
cd FIT4110_Buoi04_Docker
npm install
```

---

## 3. Build và chạy toàn bộ stack

```bash
docker compose up -d --build
```

Lệnh này tạo 3 container:

| Container | Port host | Healthcheck |
|---|---|---|
| `fit4110-ai-vision-lab04` | 8000 | `GET /health` |
| `fit4110-core-mock-lab04` | 4012 | `GET /health` |
| `fit4110-camera-mock-lab04` | 4014 | `GET /health` |

Container chạy với user non-root (`appuser:appgroup`) và share network `smartcampus-lab-net`. Trong network đó, các service resolve qua tên:
- `http://ai-vision:8000`
- `http://core-business-mock:4012`
- `http://camera-stream-mock:4014`

---

## 4. Kiểm tra nhanh `/health`

Mở terminal khác:

```bash
curl http://localhost:8000/health
curl http://localhost:4012/health
curl http://localhost:4014/health
```

Kết quả kỳ vọng:

```jsonc
// AI Vision
{"status":"ok","service":"ai-vision","version":"1.0.0","modelLoaded":true,"modelVersion":"yolov8n-v1.0","time":"..."}

// Core Business mock
{"status":"ok","service":"core-business-mock","time":"..."}

// Camera Stream mock
{"status":"ok","service":"camera-stream-mock","time":"..."}
```

---

## 5. Chạy Newman collection trên AI Vision container

```bash
npm run test:vision:local
```

Report sinh ra tại:

```text
reports/newman-vision-local.html
reports/newman-vision-local.xml
```

---

## 6. Gọi AI Vision service bằng tay (Bearer token mặc định `local-dev-token-vision`)

```bash
# Detect (image_url)
curl -X POST http://localhost:8000/vision/detect \
  -H "Authorization: Bearer local-dev-token-vision" \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"cam-gate-01","image_url":"http://storage.campus.local/images/frame-001.jpg","timestamp":"2026-08-11T10:30:00Z","confidence_threshold":0.6}'

# Lấy model info
curl http://localhost:8000/vision/models/info \
  -H "Authorization: Bearer local-dev-token-vision"
```

Gọi core-business-mock để verify integration end-to-end:

```bash
curl -X POST http://localhost:4012/policies/evaluate-detection \
  -H "Authorization: Bearer lab-token-core" \
  -H "Content-Type: application/json" \
  -d '{"detection_id":"0196fb3d-4ad7-7d1e-9f49-5d5148d2babc","camera_id":"cam-gate-01","risk_level":"HIGH","timestamp":"2026-08-11T10:30:01Z"}'
```

---

## 7. Dừng stack

```bash
docker compose down
```

Nếu muốn xoá luôn image:

```bash
docker compose down --rmi all
```

---

## 8. Lệnh nhanh qua Makefile

```bash
make build     # docker compose build
make up        # docker compose up -d --build
make down      # docker compose down
make ps        # docker compose ps
make logs      # xem log
make health    # curl /health của 3 service
make test-vision-local   # npm run test:vision:local
make lint      # spectral lint contracts/ai-vision.openapi.yaml
make clean     # down stack + xoá image + reports
```
