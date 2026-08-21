# Consumer–Provider Handshake — FIT4110 Lab 03

## Thông tin chung

- Lab: FIT4110 Lab 03
- Ngày: 2026-08-13
- Team: `team-vision` (AI Vision Service)

---

## 1. Handshake #1 — AI Vision (Provider) ↔ Camera Stream (Consumer)

| Trường | Giá trị |
|---|---|
| Provider team | team-vision |
| Consumer team | team-camera |
| Provider service | AI Vision Service |
| Consumer service | Camera Stream Service |
| Contract file | `contracts/ai-vision.openapi.yaml` |
| Mock base URL | `http://localhost:4011` (Prism mock AI Vision) |
| Auth method | Bearer JWT — header `Authorization: Bearer <token>` |
| Endpoint được test | `POST /vision/detect` |

### Smoke test

#### Request

```http
POST http://localhost:4011/vision/detect
Authorization: Bearer lab-token-vision
Content-Type: application/json

{
  "camera_id": "cam-gate-01",
  "image_url": "http://storage.campus.local/images/frame-001.jpg",
  "timestamp": "2026-08-13T07:30:00Z",
  "confidence_threshold": 0.6
}
```

#### Expected response

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

Response headers: `X-Detection-Id`, `X-Processing-Time-Ms`.

### Kết quả (đã chạy trong Newman)

- [x] Consumer gọi mock thành công (`POST /vision/detect` → 200 trên cả Prism mock và service thật).
- [x] Consumer parse được field cần dùng (`detection_id`, `detections`, `risk_level`).
- [x] Consumer hiểu lỗi 4xx/5xx provider trả về (đã test 422 cho missing camera_id, 401 cho missing/invalid token, 404 cho detection_id không tồn tại).
- [x] Có Newman report: `reports/vision-newman-report-mock.html`, `reports/vision-newman-report-local.html`.

---

## 2. Handshake #2 — Core Business (Consumer) ↔ AI Vision (Provider)

| Trường | Giá trị |
|---|---|
| Provider team | team-vision |
| Consumer team | team-core |
| Provider service | AI Vision Service |
| Consumer service | Core Business Service |
| Contract file | `contracts/ai-vision.openapi.yaml` |
| Mock base URL | `http://localhost:4011` (Prism mock AI Vision) |
| Auth method | Bearer JWT |
| Endpoint được test | `POST /vision/face-match`, `GET /vision/results/recent` |

### Smoke test

#### Request #1 — face-match (Core xác minh người trước camera)

```http
POST http://localhost:4011/vision/face-match
Authorization: Bearer lab-token-vision
Content-Type: application/json

{
  "image_url": "http://storage.campus.local/images/face-detected.jpg",
  "reference_image_url": "http://storage.campus.local/profiles/student-sv001.jpg",
  "threshold": 0.75,
  "trace_id": "trace-20260813-001",
  "timestamp": "2026-08-13T07:30:00Z"
}
```

#### Expected response

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
  "trace_id": "trace-20260813-001",
  "timestamp": "2026-08-13T07:30:02Z"
}
```

Response header: `X-Trace-Id`.

#### Request #2 — recent detections (Core tổng hợp analytics)

```http
GET http://localhost:4011/vision/results/recent?limit=20&camera_id=cam-gate-01
Authorization: Bearer lab-token-vision
```

### Kết quả

- [x] Consumer gọi mock thành công (face-match 200 trên cả mock và service thật; recent trả items array với pagination).
- [x] Consumer parse được field cần dùng (`match_id`, `matched`, `status`, `items[]`).
- [x] Consumer hiểu lỗi 4xx (đã test 422 cho face-match thiếu reference, 401 cho thiếu token).
- [x] Có Newman report: `reports/vision-newman-report-mock.html`, `reports/vision-newman-report-local.html`.

---

## 3. Ghi chú thay đổi hợp đồng

| Nội dung | Trước | Sau | Người đồng ý |
|---|---|---|---|
| Thêm `processing_time_ms` tối thiểu 0 (đã có) | ≥ 0 | ≥ 0 | team-vision |
| Thêm `TooManyRequests (429)` vào tất cả endpoint | thiếu | đã thêm | team-vision |
| Đổi `image_url` sang format URI chuẩn | string | format: uri | team-vision |
| Thêm `instance` field cho ProblemDetails | optional | optional (không bắt buộc cho mọi response) | team-vision |

## 4. Xác nhận

- Provider representative: team-vision (ai-vision@smart-campus.edu.vn)
- Consumer representative: team-core, team-camera (sẽ xác nhận khi nhận bàn giao)

## 5. Phạm vi smoke test thực tế (đã chạy)

- Mock của provider: Prism mock AI Vision (`npm run mock:vision`) — đã verify 6 endpoint.
- Mock của consumer do team-vision cung cấp:
  - Camera Stream mock: `npm run serve:camera-mock` (port 4014) — endpoints `/health`, `POST /frames`, `GET /cameras/{id}/frames/latest`.
  - Core Business mock: `npm run serve:core-mock` (port 4012) — endpoints `/health`, `GET /alerts/recent`, `POST /policies/evaluate-detection`.
- Newman chạy thành công **23 requests / 49 assertions / 0 failure** trên cả 2 môi trường:
  - Mock: `reports/vision-newman-report-mock.{xml,html}`
  - Local service thật: `reports/vision-newman-report-local.{xml,html}`
