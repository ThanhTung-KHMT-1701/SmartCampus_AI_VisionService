# Consumer–Provider Handshake — Team Vision (AI Vision)
## FIT4110 Lab 05 — Docker Service

## Thông tin chung

- Lab: FIT4110 Lab 05
- Ngày: 2026-08-25
- Provider team: team-vision
- Consumer team 1: team-camera (Camera Stream)
- Consumer team 2: team-core (Core Business)
- Provider service: AI Vision Service (Dockerized)
- Consumer service 1: Camera Stream Service (chạy ngoài Docker, LAN IP)
- Consumer service 2: Core Business Service (chạy ngoài Docker, LAN IP)

## Contract

- Contract file: `FIT4110_Buoi03_Postman_Mock_Testing/contracts/ai-vision.openapi.yaml`
- Provider base URL (Docker): `http://localhost:8000`
- Provider base URL (LAN remote): `http://<HOST-IP>:8000`
- Auth method: Bearer token (đọc từ `AI_VISION_AUTH_TOKEN` env var; default `local-dev-token-vision`)
- Public endpoint: `GET /health` (no auth required)
- Endpoints được test:
  - `GET /health` — Health check
  - `POST /vision/detect` — Phát hiện đối tượng
  - `GET /vision/detections/{detection_id}` — Lấy detection theo UUID
  - `GET /vision/results/recent` — Lấy danh sách detections gần đây
  - `POST /vision/face-match` — So khớp khuôn mặt
  - `GET /vision/models/info` — Thông tin model AI

## Sự khác biệt so với Buổi 3

Buổi 3: gọi **Prism mock** (`:4011`) — không kiểm chứng được auth và validation thật.
Buổi 5: gọi **Docker service thật** (`:8000`) — auth và validation được FastAPI/Pydantic enforce.

| Hành vi | Buổi 3 (mock) | Buổi 5 (Docker) |
|---|---|---|
| Auth thật | Bị skip | **Thật** — 401 nếu sai token |
| Validation | Chỉ check shape | **Thật** — FastAPI/Pydantic validate |
| Header `X-Detection-Id` | Không có | **Có** |
| Header `X-Processing-Time-Ms` | Không có | **Có** |
| Header `X-Trace-Id` (face-match) | Không có | **Có** |
| ProblemDetails (RFC 9457) | Tùy mock | **Có** — `application/problem+json` |

## Pair 01 — Camera Stream (team-camera) → AI Vision (team-vision)

### Smoke test (consumer-side)

#### Request

```http
POST http://192.168.137.115:8001/frames
Authorization: Bearer lab-token-camera
Content-Type: application/json
```

```json
{
  "camera_id": "cam-lab05-e2e",
  "frame_url": "http://192.168.137.115:8001/cameras/cam-lab05-e2e/frames/latest",
  "motion_detected": true,
  "timestamp": "2026-08-25T08:45:00Z"
}
```

#### Expected response (2xx)

```json
{
  "frame_id": "frame-20260825-084500-xyz789",
  "status": "accepted",
  "timestamp": "2026-08-25T08:45:01Z",
  "message": "Frame accepted for processing"
}
```

Sau đó, **AI Vision Docker** được gọi:

```http
POST http://localhost:8000/vision/detect
Authorization: Bearer local-dev-token-vision
Content-Type: application/json
X-Trace-Id: trace-lab05-001
```

```json
{
  "camera_id": "cam-lab05-gate",
  "image_url": "http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest",
  "timestamp": "2026-08-25T08:00:00Z",
  "confidence_threshold": 0.6
}
```

#### Expected response (200)

```json
{
  "detection_id": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc",
  "camera_id": "cam-lab05-gate",
  "detections": [
    {
      "label": "person",
      "confidence": 0.95,
      "bbox": {"x": 100, "y": 50, "width": 80, "height": 150},
      "class_id": 0
    }
  ],
  "risk_level": "LOW",
  "model_version": "yolov8n-v1.0",
  "processing_time_ms": 45,
  "timestamp": "2026-08-25T08:00:01Z"
}
```

### Kết quả

- [x] Consumer gọi Camera Stream mock thành công (POST /frames trả 2xx).
- [x] Consumer gọi AI Vision Docker thành công (POST /vision/detect trả 200).
- [x] Consumer parse được detection_id, detections[], bbox, confidence, risk_level.
- [x] Consumer hiểu lỗi 4xx/5xx — ProblemDetails RFC 9457.
- [x] Có Newman report (`reports/vision-newman-report-docker-latest.html`).

## Pair 02 — Core Business (team-core) → AI Vision (team-vision)

### Smoke test (consumer-side)

#### Request

```http
POST http://localhost:8000/vision/face-match
Authorization: Bearer local-dev-token-vision
Content-Type: application/json
X-Trace-Id: trace-lab05-002
```

```json
{
  "image_url": "http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest",
  "reference_image_url": "http://192.168.137.79:8001/profiles/student-001.jpg",
  "threshold": 0.75,
  "trace_id": "trace-lab05-002",
  "timestamp": "2026-08-25T08:30:00Z"
}
```

#### Expected response (200)

```json
{
  "match_id": "0196fb3d-4ad7-7d1e-9f49-5d5148d2bc01",
  "matched": true,
  "confidence": 0.93,
  "threshold": 0.75,
  "status": "MATCHED",
  "message": "Khuôn mặt khớp với độ tin cậy cao",
  "model_version": "facenet-v1.2",
  "processing_time_ms": 120,
  "trace_id": "trace-lab05-002",
  "timestamp": "2026-08-25T08:30:02Z"
}
```

### Kết quả

- [x] Consumer gọi AI Vision Docker thành công (POST /vision/face-match trả 200).
- [x] Consumer parse được matched, confidence, status, trace_id.
- [x] Consumer hiểu lỗi 4xx/5xx — ProblemDetails RFC 9457.
- [x] Có Newman report (`reports/vision-newman-report-docker-latest.html`).

## Ghi chú thay đổi hợp đồng (so với Buổi 3)

| Nội dung | Buổi 3 | Buổi 5 | Lý do |
|---|---|---|---|
| Provider location | Prism mock :4011 | **Docker container :8000** | Test service thật |
| Auth middleware | Không có | **Có (thật)** | FastAPI từ chối token sai |
| Validation middleware | Mock | **Pydantic (thật)** | 422 ProblemDetails khi sai schema |
| Header `X-Detection-Id` | Không có | **Có** | Trả về detection_id qua header |
| Header `X-Processing-Time-Ms` | Không có | **Có** | Tiện cho monitoring |
| Header `X-Trace-Id` (face-match) | Không có | **Có (echo từ request)** | Distributed tracing |
| Media type lỗi | `application/json` | **`application/problem+json`** | RFC 9457 |
| Endpoint `/vision/results/recent` | Optional | **Có** | Filter `camera_id`, paginate cursor |

## Xác nhận

- Provider representative: team-vision (AI Vision Service)
- Consumer representative 1: team-camera (Camera Stream Service)
- Consumer representative 2: team-core (Core Business Service)

## Mock / Docker commands

- Start AI Vision Docker: `docker compose up -d`
- Stop AI Vision Docker: `docker compose down`
- Run Newman: `npm run test:lab05` (sau khi `npm install -g newman`)
- Run smoke test: `.\scripts\contract-smoke.ps1`
- Run 18 test cases: `.\scripts\run-18-test-cases.ps1`
- Collect evidence: `.\scripts\collect-evidence.ps1`
