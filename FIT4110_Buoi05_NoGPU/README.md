# FIT4110 — Buổi 05: Docker Compose Readiness (AI VisionService, NoGPU)

Repo này là bài nộp Lab 05 của nhóm **team-vision** (AI VisionService) thuộc môn
FIT4110 — Dịch vụ kết nối & Công nghệ nền tảng (Smart Campus Operations Platform).

## Mục tiêu

Mở rộng Lab 04 (Docker packaging đơn lẻ) sang **docker-compose** với 3 service:

- `ai-vision` — REST API (FastAPI) — entry point cho Camera Stream và Core Business.
- `ai-yolo` — Inference service chạy YOLOv8n trên **CPU** (không yêu cầu GPU).
- `vision-db` — Postgres 16-alpine dùng cho audit log (sidecar).

Stack giao tiếp qua mạng `team-internal`; plug vào mạng `class-net` để sẵn sàng
plug-a-thon.

## Cấu trúc

```
FIT4110_Buoi05_NoGPU/
├── README.md
├── RUN_COMPOSE.md            # Hướng dẫn chạy stack cho người mới
├── docker-compose.yml        # 3 service + 2 network + 2 volume
├── Dockerfile                # API service (multi-stage, non-root)
├── Dockerfile.yolo           # YOLO service (multi-stage, non-root)
├── Dockerfile.db             # Postgres sidecar
├── .dockerignore             # build context hygiene
├── .env.example              # runtime config template
├── Makefile                  # compose-up, test-local, test-compose, ...
├── requirements.txt          # API service deps
├── requirements-yolo.txt     # YOLO service deps (ultralytics + torch CPU)
├── package.json              # npm scripts: serve, test:mock/local/compose
├── contracts/
│   └── ai-vision.openapi.yaml # OpenAPI 3.1 cho cả API + readiness
├── src/
│   ├── ai_vision_service/    # API
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── store.py          # SQLite-backed persistence
│   │   └── yolo_adapter.py   # gọi sang YOLO service
│   └── ai_yolo_service/      # YOLO inference
│       ├── __init__.py
│       └── main.py
├── postman/
│   ├── collections/
│   │   └── FIT4110_lab05_ai_vision.postman_collection.json
│   └── environments/
│       ├── FIT4110_lab05_ai_vision_local.postman_environment.json
│       ├── FIT4110_lab05_ai_vision_compose.postman_environment.json
│       └── FIT4110_lab05_ai_vision_mock.postman_environment.json
├── checklists/
│   └── readiness-checklist.md
├── docs/
│   └── TEAM_TASKS.md
├── mock-data/
│   └── detect-valid.json
└── reports/
    └── evidence/             # log, html, xml, screenshots
```

## Tính năng mới so với Lab 04

| Tính năng | Mô tả |
|---|---|
| `/ready` | Readiness check tổng hợp — Docker Compose dùng để gate traffic |
| YOLOv8 inference | Service riêng (`ai-yolo`) — Ultralytics YOLOv8n trên CPU |
| SQLite persistence | Detection & face-match sống sót qua container restart |
| Postgres sidecar | `vision-db` cho audit, có healthcheck riêng |
| Multi-network | `team-internal` (private) + `class-net` (external cho plug-a-thon) |
| Header `X-Yolo-Mode` | Client biết được inference đang ở chế độ inproc/remote/stub |

## Chạy nhanh

```bash
npm install
make compose-up
make health
make ready
make test-compose
```

Xem chi tiết trong `RUN_COMPOSE.md`.

## Báo cáo

Toàn bộ log build, log container, response `/health`, `/ready` và Newman report
được lưu trong `reports/`. Báo cáo tổng hợp từng bước ở `REPORT.md`.

## Liên hệ

- Nhóm: team-vision (AI VisionService)
- Stack: FastAPI + Ultralytics YOLOv8n (CPU) + SQLite + Postgres
- Môn: FIT4110 — Dịch vụ kết nối và Công nghệ nền tảng