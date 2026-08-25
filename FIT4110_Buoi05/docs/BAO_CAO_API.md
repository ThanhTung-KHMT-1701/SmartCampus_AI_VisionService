# BÁO CÁO API — AI Vision Service
## FIT4110 Buổi 5

Tài liệu tham chiếu nhanh cho tất cả endpoints của AI Vision Service (Docker).

---

## Endpoint 1: `GET /health`

**Auth:** Không yêu cầu (public).

**Mô tả:** Health check — dùng để verify Docker container đang chạy.

**Response (200):**
```json
{
  "status": "ok",
  "service": "ai-vision",
  "version": "1.0.0",
  "modelLoaded": true,
  "modelVersion": "yolov8n-v1.0",
  "time": "2026-08-25T08:00:00Z"
}
```

**Test:**
```powershell
curl.exe http://localhost:8000/health
```

---

## Endpoint 2: `POST /vision/detect`

**Auth:** Bearer token (khớp với `AI_VISION_AUTH_TOKEN`).
**Mặc định token:** `local-dev-token-vision`.

**Mô tả:** Phát hiện đối tượng trong ảnh (YOLO stub). Lưu kết quả vào in-memory store.

**Request body:**
```json
{
  "camera_id": "cam-lab05-gate",
  "image_url": "http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest",
  "timestamp": "2026-08-25T08:00:00Z",
  "confidence_threshold": 0.6
}
```

Lưu ý:
- `image_url` và `image_base64` **mutually exclusive** — chỉ một trong hai.
- `camera_id` phải match pattern `^[a-z0-9-]+$`.
- `confidence_threshold` ∈ [0, 1], optional.

**Response (200):**
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

**Headers phản hồi:**
- `X-Detection-Id: <uuid>`
- `X-Processing-Time-Ms: <int>`

**Risk levels:**
- `<2 detections` → `LOW`
- `2-4 detections` → `MEDIUM`
- `>=5 detections` → `HIGH`

**Lỗi:**
| Code | Nguyên nhân |
|---|---|
| 401 | Missing/wrong token |
| 422 | Validation error (ProblemDetails) |

**Test:**
```powershell
curl.exe -X POST http://localhost:8000/vision/detect `
  -H "Authorization: Bearer local-dev-token-vision" `
  -H "Content-Type: application/json" `
  -d '{"camera_id":"cam-lab05-gate","image_url":"http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest","timestamp":"2026-08-25T08:00:00Z"}'
```

---

## Endpoint 3: `GET /vision/detections/{detection_id}`

**Auth:** Bearer token.

**Mô tả:** Lấy detection record theo UUID.

**Response (200):** giống `DetectResponse`.

**Lỗi:**
| Code | Nguyên nhân |
|---|---|
| 401 | Missing/wrong token |
| 404 | UUID không tồn tại trong store |
| 422 | UUID không đúng format |

**Test:**
```powershell
curl.exe -H "Authorization: Bearer local-dev-token-vision" http://localhost:8000/vision/detections/0196fb3d-4ad7-7d1e-9f49-5d5148d2babc
```

---

## Endpoint 4: `GET /vision/results/recent`

**Auth:** Bearer token.

**Mô tả:** List detection gần nhất (max 100 record).

**Query params:**
| Tên | Type | Default | Ràng buộc |
|---|---|---|---|
| `limit` | int | 20 | 1 ≤ limit ≤ 100 |
| `cursor` | string | null | max 200 chars |
| `camera_id` | string | null | match `^[a-z0-9-]+$` |
| `from_time` | ISO 8601 | null | |
| `to_time` | ISO 8601 | null | |

**Response (200):**
```json
{
  "items": [
    {
      "detection_id": "...",
      "camera_id": "cam-lab05-gate",
      "detections": [...],
      "risk_level": "LOW",
      "model_version": "yolov8n-v1.0",
      "processing_time_ms": 45,
      "timestamp": "2026-08-25T08:00:01Z"
    }
  ],
  "nextCursor": "MjAyNi0wOC0yNVQwODowMDowMVo=",
  "hasMore": false
}
```

**Test:**
```powershell
curl.exe -H "Authorization: Bearer local-dev-token-vision" "http://localhost:8000/vision/results/recent?limit=10&camera_id=cam-lab05-gate"
```

---

## Endpoint 5: `POST /vision/face-match`

**Auth:** Bearer token.

**Mô tả:** So khớp khuôn mặt (FaceNet stub). Confidence mặc định 0.93; nếu threshold ≥ 0.9 thì confidence giảm xuống 0.45 (mô phỏng kém khớp).

**Request body:**
```json
{
  "image_url": "http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest",
  "reference_image_url": "http://192.168.137.79:8001/profiles/student-001.jpg",
  "threshold": 0.75,
  "trace_id": "trace-lab05-001",
  "timestamp": "2026-08-25T08:30:00Z"
}
```

Yêu cầu:
- `image_url` XOR `image_base64`
- `reference_image_url` XOR `reference_image_base64`
- `threshold` ∈ [0, 1], default 0.7

**Response (200):**
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
  "trace_id": "trace-lab05-001",
  "timestamp": "2026-08-25T08:30:02Z"
}
```

**Status enum:**
- `MATCHED` — confidence >= threshold
- `LOW_CONFIDENCE` — confidence ∈ [0.6, threshold)
- `NOT_MATCHED` — confidence < 0.6

**Header phản hồi:** `X-Trace-Id: <echo>`

---

## Endpoint 6: `GET /vision/models/info`

**Auth:** Bearer token.

**Mô tả:** Thông tin metadata về AI model.

**Response (200):**
```json
{
  "model_id": "yolov8n-v1.0",
  "model_type": "object_detection",
  "framework": "ultralytics",
  "framework_version": "8.3.0",
  "classes": [
    {"id": 0, "name": "person", "description": "Con người"},
    {"id": 2, "name": "car", "description": "Ô tô"},
    {"id": 3, "name": "motorcycle", "description": "Xe máy"},
    {"id": 15, "name": "cat", "description": "Mèo"},
    {"id": 16, "name": "dog", "description": "Chó"}
  ],
  "confidence_threshold_default": 0.5,
  "input_size": 640,
  "accuracy_map": 0.73,
  "inference_time_ms_avg": 35,
  "last_updated": "2026-07-15T00:00:00Z",
  "status": "ACTIVE"
}
```

---

## Error Format (RFC 9457 — ProblemDetails)

Mọi lỗi 4xx/5xx trả về theo format:
```json
{
  "type": "https://ai-vision.campus.local/errors/<status>",
  "title": "<short description>",
  "status": 422,
  "detail": "<human-readable detail>",
  "errors": [
    {
      "field": "camera_id",
      "code": "string_pattern_mismatch",
      "message": "String should match pattern '^[a-z0-9-]+$'"
    }
  ]
}
```

Content-Type: `application/problem+json`

---

## Tổng kết

| Endpoint | Method | Auth | Status range |
|---|---|---|---|
| `/health` | GET | public | 200 |
| `/vision/detect` | POST | required | 200 / 401 / 422 |
| `/vision/detections/{id}` | GET | required | 200 / 401 / 404 / 422 |
| `/vision/results/recent` | GET | required | 200 / 401 / 422 |
| `/vision/face-match` | POST | required | 200 / 401 / 422 |
| `/vision/models/info` | GET | required | 200 / 401 |

---

*Báo cáo API — FIT4110 Buổi 5 — 2026-08-25*
