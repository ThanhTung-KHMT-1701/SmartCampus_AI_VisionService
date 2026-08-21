# Consumer–Provider Handshake — Team Vision (AI Vision)

## Thông tin chung

- Lab: FIT4110 Lab 03
- Ngày: 2026-08-13
- Provider team: team-vision
- Consumer team 1: team-camera (Camera Stream)
- Consumer team 2: team-core (Core Business)
- Provider service: AI Vision Service
- Consumer service 1: Camera Stream Service
- Consumer service 2: Core Business Service

## Contract

- Contract file: `contracts/ai-vision.openapi.yaml`
- Mock base URL: `http://localhost:4011`
- Auth method: Bearer JWT (POST /vision/detect, POST /vision/face-match, GET endpoints)
- Public endpoint: `GET /health` (no auth required)
- Endpoints được test:
  - `GET /health` — Health check
  - `POST /vision/detect` — Phát hiện đối tượng
  - `GET /vision/detections/{detectionId}` — Lấy detection theo ID
  - `GET /vision/results/recent` — Lấy danh sách detections gần đây
  - `POST /vision/face-match` — So khớp khuôn mặt
  - `GET /vision/models/info` — Thông tin model AI

## Pair 01 — Camera Stream (team-camera) → AI Vision (team-vision)

### Smoke test

#### Request

```http
POST /vision/detect
Authorization: Bearer {{authToken}}
Content-Type: application/json
X-Trace-Id: trace-20260813-001
```

```json
{
  "camera_id": "cam-gate-01",
  "image_url": "http://storage.campus.local/images/frame-001.jpg",
  "timestamp": "2026-08-13T07:30:00Z",
  "confidence_threshold": 0.6
}
```

#### Expected response (200)

```json
{
  "detection_id": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc",
  "camera_id": "cam-gate-01",
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
  "timestamp": "2026-08-13T07:30:01Z"
}
```

### Kết quả

- [x] Consumer gọi mock thành công (POST /vision/detect trả 200).
- [x] Consumer parse được field cần dùng (detections[], bbox, confidence, risk_level).
- [x] Consumer hiểu lỗi 4xx/5xx provider trả về (ProblemDetails).
- [x] Có Newman report (reports/vision-newman-report-mock.xml).

## Pair 02 — Core Business (team-core) → AI Vision (team-vision)

### Smoke test

#### Request

```http
POST /vision/face-match
Authorization: Bearer {{authToken}}
Content-Type: application/json
X-Trace-Id: trace-20260813-002
```

```json
{
  "image_url": "http://storage.campus.local/images/face-detected.jpg",
  "reference_image_url": "http://storage.campus.local/profiles/student-001.jpg",
  "threshold": 0.75,
  "trace_id": "trace-20260813-002",
  "timestamp": "2026-08-13T07:30:00Z"
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
  "trace_id": "trace-20260813-002",
  "timestamp": "2026-08-13T07:30:02Z"
}
```

### Kết quả

- [x] Consumer gọi mock thành công (POST /vision/face-match trả 200).
- [x] Consumer parse được field cần dùng (matched, confidence, status, trace_id).
- [x] Consumer hiểu lỗi 4xx/5xx provider trả về (ProblemDetails).
- [x] Có Newman report (reports/vision-newman-report-mock.xml).

## Ghi chú thay đổi hợp đồng

| Nội dung | Trước | Sau | Người đồng ý |
|---|---|---|---|
| Path prefix thêm `/vision/` | `/detect` | `/vision/detect` | team-vision, team-camera, team-core |
| Thêm endpoint GET /vision/detections/{id} | Không có | Có | team-vision |
| Thêm endpoint GET /vision/results/recent | Không có | Có | team-core (cần cho dashboard) |
| Schema enum cho `risk_level` | Không ràng buộc | LOW/MEDIUM/HIGH/CRITICAL | team-vision |
| Schema enum cho `label` | Mở | person/car/truck/motorcycle/bicycle/dog/cat/backpack/handbag | team-vision |
| Thêm `confidence_threshold` mặc định 0.5 | Không có | Có | team-vision, team-camera |
| Thêm `X-Trace-Id` header | Không có | Có (optional) | team-vision (cho distributed tracing) |

## Xác nhận

- Provider representative: team-vision (AI Vision Service)
- Consumer representative 1: team-camera (Camera Stream Service)
- Consumer representative 2: team-core (Core Business Service)

## Mock commands

- Start AI Vision mock: `npm run mock:vision`
- Start cùng lúc nhiều mock (IoT + Vision): `npm run mock:all`
- Chạy Newman trên mock: `npm run test:vision:mock`
- Chạy Newman trên local: `npm run test:vision:local`
- Lint contract: `npm run lint:vision`
- CI pipeline: `npm run test:ci:vision`
