# Docker Compose Readiness Checklist — Lab 05 (team-vision, NoGPU YOLOv8)

## Stack

- [x] `docker-compose.yml` định nghĩa ≥3 service: `ai-vision`, `ai-yolo`, `vision-db`.
- [x] Có 2 network: `team-internal` (private) và `class-net` (external, dùng cho plug-a-thon).
- [x] Có 2 named volume: `smartcampus-vision-data` (SQLite), `smartcampus-vision-pg` (Postgres).
- [x] Mỗi service có `healthcheck` riêng (AI vision: `/health`, YOLO: `/health`, DB: `pg_isready`).
- [x] `depends_on` dùng `condition: service_healthy` — `ai-vision` chỉ start khi YOLO và DB đã ready.

## Dockerfile

- [x] Multi-stage build (`builder` → `runtime`) để image nhỏ.
- [x] Image gốc: `python:3.11-slim` (AI), `python:3.11-slim` (YOLO), `postgres:16-alpine` (DB).
- [x] Container chạy non-root (`appuser:appgroup` cho AI + YOLO, `postgres` user mặc định cho DB).
- [x] HEALTHCHECK có trong Dockerfile AI + YOLO (DB có HEALTHCHECK riêng trong Dockerfile.db).
- [x] Không có secret thật trong image — chỉ default dev, override qua `.env`.

## Runtime

- [x] Port mapping: 8000 (API), 9000 (YOLO), 5432 (DB internal — không publish ra host).
- [x] ENV tách qua `.env.example`: `AI_VISION_AUTH_TOKEN`, `YOLO_*`, `VISION_DB_*`.
- [x] `/health` trả 200 cho cả AI + YOLO.
- [x] `/ready` (AI) trả 200 khi cả `sqlite` + `ai-yolo` đều `up`; 503 nếu một trong hai `down`.

## Testing

- [x] Newman chạy được trên cả local (`test:local`) và compose (`test:compose`).
- [x] Functional: 5/5 pass (detect, detect-by-id, recent, face-match, models/info).
- [x] Auth: 401 cho missing token và wrong token.
- [x] Negative: 422 cho mutually-exclusive và missing field.
- [x] Boundary: threshold 0.0/1.0/1.5.
- [x] Compose readiness: `/ready` có deps, YOLO `/predict` trả 200 với detections.

## Evidence (trong `reports/`)

- [x] Log `docker compose build` → `reports/compose-build.log`
- [x] Log `docker compose ps` → `reports/compose-ps.txt`
- [x] 3 response `/health` → `reports/health-api.json`, `reports/health-yolo.json`, `reports/pg-isready.txt`
- [x] `/ready` response → `reports/ready.json`
- [x] Newman HTML/XML → `reports/newman-lab05-{local,compose}.{html,xml}`
- [x] Tag image: `fit4110/ai-vision:lab05`, `fit4110/ai-yolo:lab05`, `fit4110/vision-db:lab05`

## Tinh thần

- [x] Stack chạy được end-to-end bằng một lệnh (`make compose-up`).
- [x] Người khác clone repo có thể chạy lại chỉ với Docker + Node (xem `RUN_COMPOSE.md`).
- [x] Không leak secret; `.env.example` là template công khai.