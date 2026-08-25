# RUN_COMPOSE — FIT4110 Lab 05 (AI VisionService, team-vision)

Hướng dẫn này giúp người khác clone repo và chạy lại toàn bộ stack Compose trong vài phút.

## 1. Yêu cầu

- Docker Desktop / Docker Engine ≥ 24 với Compose v2.
- Node.js 20.x LTS + npm (chỉ cần nếu muốn chạy Newman/Prism/Spectral).
- Tùy chọn: Postman Desktop để mở collection trong `postman/collections/`.

Kiểm tra:

```bash
docker compose version
docker --version
node --version
npx newman --version
```

## 2. Clone & cài dependencies

```bash
git clone <repo-url> FIT4110_Buoi05_NoGPU
cd FIT4110_Buoi05_NoGPU
npm install
cp .env.example .env   # chỉnh token nếu cần
```

## 3. Chạy stack Compose

```bash
make compose-up
# tương đương: docker compose up -d --build
```

Quá trình:

1. Build image `fit4110/ai-yolo:lab05` (CPU, có Ultralytics).
2. Build image `fit4110/ai-vision:lab05` (FastAPI, gọi sang YOLO container).
3. Build image `fit4110/vision-db:lab05` (Postgres 16-alpine).
4. Khởi động theo thứ tự: `ai-yolo` & `vision-db` song song → `ai-vision` chỉ start khi cả hai healthy.

## 4. Kiểm tra readiness

```bash
make health
make ready
```

`/ready` trả:

```json
{
  "status": "ready",
  "service": "ai-vision",
  "version": "0.5.0",
  "dependencies": [
    {"name": "sqlite", "status": "up", "detail": "detections=3, face_matches=1"},
    {"name": "ai-yolo", "status": "up", "detail": "version=0.5.0, mode=stub"}
  ],
  "time": "2026-08-22T..."
}
```

## 5. Mở Swagger UI

http://localhost:8000/docs

## 6. Chạy Postman/Newman

```bash
make test-compose
```

Reports được sinh ra tại `reports/newman-lab05-compose.{html,xml}`.

## 7. Dừng stack & dọn dẹp

```bash
make compose-down      # dừng + xóa container
make clean             # kèm xóa image và volume
```

## 8. Chạy local không qua Docker (tùy chọn)

```bash
python -m venv .venv
. .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-yolo.txt
npm run serve:yolo &       # port 9000
YOLO_SERVICE_URL=http://localhost:9000 npm run serve:vision
make test-local
```

## 9. Troubleshooting

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `ai-vision` exit ngay | YOLO chưa healthy | `docker compose logs ai-yolo` — chờ healthcheck |
| `/ready` 503 — `ai-yolo down` | sai URL hoặc YOLO chưa start | kiểm tra `YOLO_SERVICE_URL` |
| `/ready` 503 — `sqlite down` | volume `/data` chưa mount | `docker compose down` rồi `make compose-up` |
| Newman 401 | token khác env | set `authToken` trong environment |
| Image quá nặng | torch CPU kéo về ~1GB | chấp nhận cho lab; tối ưu bằng `python:slim` đã làm |

## 10. Liên hệ

Nhóm team-vision, FIT4110 — Smart Campus Operations Platform.