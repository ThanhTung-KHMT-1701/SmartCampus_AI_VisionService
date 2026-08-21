# BÁO CÁO KIỂM THỬ API — AI Vision Service
## FIT4110 Buổi 3 — Smart Campus Operations Platform

**Team:** team-vision
**Service:** AI Vision Service
**Hợp đồng:** `contracts/ai-vision.openapi.yaml` (OpenAPI 3.1)
**Công cụ:** Newman CLI 5.3.0, Postman Collection
**Ngày:** 2026-08-13

---

## 1. Tổng quan API

AI Vision Service cung cấp **6 endpoints** theo OpenAPI spec:

| Method | Endpoint | Mô tả | Auth | Request Body |
|---|---|---|---|---|
| GET | `/health` | Health check | ❌ Public | — |
| POST | `/vision/detect` | Phát hiện đối tượng | ✅ Bearer | `DetectRequest` |
| GET | `/vision/detections/{detectionId}` | Lấy detection theo ID | ✅ Bearer | — |
| GET | `/vision/results/recent` | Danh sách detection gần đây | ✅ Bearer | — |
| POST | `/vision/face-match` | So khớp khuôn mặt | ✅ Bearer | `FaceMatchRequest` |
| GET | `/vision/models/info` | Thông tin model AI | ✅ Bearer | — |

---

## 2. Chi tiết từng API

### 2.1. GET /health

**Mục đích:** Kiểm tra service còn sống, model đã load.
**Auth:** Không cần (public).
**Tested:** TC01.

#### Request

```
GET /health
```

#### Response 200 OK

```json
{
  "status": "ok",
  "service": "ai-vision",
  "version": "1.0.0",
  "modelLoaded": true,
  "modelVersion": "yolov8n-v1.0",
  "time": "2026-08-13T07:30:00Z"
}
```

| Field | Kiểu | Mô tả |
|---|---|---|
| `status` | string (enum: "ok") | Bắt buộc |
| `service` | string | Tên service |
| `version` | string | Phiên bản API |
| `modelLoaded` | boolean | Model đã load chưa |
| `modelVersion` | string/null | Phiên bản model |
| `time` | string (date-time) | Thời gian |

#### Response 503 Service Unavailable

```json
{
  "type": "https://ai-vision.campus.local/errors/service-unavailable",
  "title": "Service không khả dụng",
  "status": 503,
  "detail": "Model đang được load"
}
```

---

### 2.2. POST /vision/detect

**Mục đích:** Nhận ảnh từ Camera Stream, phát hiện đối tượng (person, car, truck...).
**Auth:** Bearer token bắt buộc.
**Tested:** TC02, TC03, TC11, TC12, TC14, TC15.

#### Request

```
POST /vision/detect
Authorization: Bearer <token>
Content-Type: application/json

{
  "camera_id": "cam-gate-01",
  "image_url": "http://storage.campus.local/images/frame-001.jpg",
  "timestamp": "2026-08-13T07:30:00Z",
  "confidence_threshold": 0.6
}
```

| Field | Kiểu | Bắt buộc | Ràng buộc |
|---|---|---|---|
| `camera_id` | string | ✅ | pattern: `^[a-z0-9-]+$`, 1-80 ký tự |
| `image_url` | string (uri) | XOR `image_base64` | null nếu dùng base64 |
| `image_base64` | string | XOR `image_url` | null nếu dùng URL |
| `timestamp` | string (date-time) | ✅ | ISO 8601 |
| `confidence_threshold` | number | ❌ | 0.0 - 1.0, default 0.5 |
| `model_version` | string | ❌ | override model version |

> ⚠️ **Lưu ý:** Phải truyền đúng 1 trong 2: `image_url` HOẶC `image_base64`. Không được để cả hai cùng null.

#### Response 200 OK

```json
{
  "detection_id": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc",
  "camera_id": "cam-gate-01",
  "detections": [
    {
      "label": "person",
      "confidence": 0.95,
      "bbox": {
        "x": 100,
        "y": 50,
        "width": 80,
        "height": 150
      },
      "class_id": 0
    }
  ],
  "risk_level": "LOW",
  "model_version": "yolov8n-v1.0",
  "processing_time_ms": 45,
  "timestamp": "2026-08-13T07:30:01Z"
}
```

**Response Headers:**

| Header | Kiểu | Mô tả |
|---|---|---|
| `X-Detection-Id` | UUID | UUID của detection |
| `X-Processing-Time-Ms` | integer | Thời gian xử lý (ms) |

**Trường `detections[]`:**

| Field | Kiểu | Ràng buộc |
|---|---|---|
| `label` | string (enum) | person, car, truck, motorcycle, bicycle, dog, cat, backpack, handbag |
| `confidence` | number | 0.0 - 1.0 |
| `bbox` | object | x, y, width, height ≥ 0 |
| `class_id` | integer | ID của class trong model |

**Trường `risk_level`:**

| Giá trị | Mô tả |
|---|---|
| `LOW` | Không có đối tượng nguy hiểm |
| `MEDIUM` | Có đối tượng cần theo dõi |
| `HIGH` | Có đối tượng nguy hiểm |
| `CRITICAL` | Nguy cơ cao cần can thiệp ngay |

#### Response 401 Unauthorized

```json
{
  "type": "https://ai-vision.campus.local/errors/unauthorized",
  "title": "Chưa xác thực",
  "status": 401,
  "detail": "Thiếu Bearer token"
}
```

#### Response 422 Unprocessable Entity (validation fail)

```json
{
  "type": "https://ai-vision.campus.local/errors/validation",
  "title": "Dữ liệu không hợp lệ",
  "status": 422,
  "detail": "Payload không khớp schema"
}
```

---

### 2.3. GET /vision/detections/{detectionId}

**Mục đích:** Truy vấn kết quả detection đã xử lý trước đó (cache 24 giờ).
**Auth:** Bearer token bắt buộc.
**Tested:** TC04, TC08, TC13.

#### Request

```
GET /vision/detections/0196fb3d-4ad7-7d1e-9f49-5d5148d2babc
Authorization: Bearer <token>
```

| Parameter | Vị trí | Kiểu | Ràng buộc |
|---|---|---|---|
| `detectionId` | path | UUID | Bắt buộc, format UUID v4 |

#### Response 200 OK

```json
{
  "detection_id": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc",
  "camera_id": "cam-gate-01",
  "detections": [...],
  "risk_level": "LOW",
  "model_version": "yolov8n-v1.0",
  "processing_time_ms": 45,
  "timestamp": "2026-08-13T07:30:01Z"
}
```

> Trả về cùng cấu trúc với POST /vision/detect response.

#### Response 404 Not Found

```json
{
  "type": "https://ai-vision.campus.local/errors/not-found",
  "title": "Không tìm thấy",
  "status": 404,
  "detail": "Detection không tồn tại"
}
```

#### Response 422 (UUID không hợp lệ)

```json
{
  "type": "https://ai-vision.campus.local/errors/validation",
  "title": "Dữ liệu không hợp lệ",
  "status": 422,
  "detail": "detection_id phải là UUID"
}
```

---

### 2.4. GET /vision/results/recent

**Mục đích:** Lấy danh sách detection results đã xử lý gần đây.
**Auth:** Bearer token bắt buộc.
**Tested:** TC05, TC14.

#### Request

```
GET /vision/results/recent?limit=10&camera_id=cam-gate-01&from_time=2026-08-13T00:00:00Z
Authorization: Bearer <token>
```

| Parameter | Vị trí | Kiểu | Bắt buộc | Ràng buộc |
|---|---|---|---|---|
| `limit` | query | integer | ❌ | 1-100, default 20 |
| `cursor` | query | string | ❌ | null hoặc string |
| `camera_id` | query | string | ❌ | pattern: `^[a-z0-9-]+$` |
| `from_time` | query | date-time | ❌ | ISO 8601 |
| `to_time` | query | date-time | ❌ | ISO 8601 |

#### Response 200 OK

```json
{
  "items": [
    {
      "detection_id": "uuid-1",
      "camera_id": "cam-gate-01",
      "detections": [...],
      "risk_level": "LOW",
      "model_version": "yolov8n-v1.0",
      "processing_time_ms": 45,
      "timestamp": "2026-08-13T07:30:01Z"
    }
  ],
  "nextCursor": null,
  "hasMore": false
}
```

| Field | Kiểu | Mô tả |
|---|---|---|
| `items` | array | Danh sách detection, tối đa `limit` phần tử |
| `nextCursor` | string/null | Cursor cho trang tiếp theo |
| `hasMore` | boolean | Còn dữ liệu tiếp không |

#### Response 422 (limit vượt max)

```json
{
  "type": "https://ai-vision.campus.local/errors/validation",
  "title": "Dữ liệu không hợp lệ",
  "status": 422,
  "detail": "Số lượng giới hạn vượt quá cho phép"
}
```

---

### 2.5. POST /vision/face-match

**Mục đích:** So khớp khuôn mặt để xác minh danh tính (sinh viên quẹt thẻ).
**Auth:** Bearer token bắt buộc.
**Tested:** TC06.

#### Request

```
POST /vision/face-match
Authorization: Bearer <token>
Content-Type: application/json

{
  "image_url": "http://storage.campus.local/images/face-detected.jpg",
  "reference_image_url": "http://storage.campus.local/profiles/student-001.jpg",
  "threshold": 0.75,
  "trace_id": "trace-20260813-001",
  "timestamp": "2026-08-13T07:30:00Z"
}
```

| Field | Kiểu | Bắt buộc | Ràng buộc |
|---|---|---|---|
| `image_url` | string (uri) | XOR base64 | Ảnh cần xác minh |
| `image_base64` | string | XOR url | Ảnh cần xác minh |
| `reference_image_url` | string (uri) | XOR base64 | Ảnh tham chiếu |
| `reference_image_base64` | string | XOR url | Ảnh tham chiếu |
| `threshold` | number | ❌ | 0.0-1.0, default 0.7 |
| `trace_id` | string | ❌ | max 100 ký tự |
| `timestamp` | string (date-time) | ✅ | ISO 8601 |

#### Response 200 OK

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

**Response Header:**

| Header | Kiểu | Mô tả |
|---|---|---|
| `X-Trace-Id` | string | Trace ID của request |

**Trường `status` enum:**

| Giá trị | Mô tả |
|---|---|
| `MATCHED` | Khuôn mặt khớp |
| `NOT_MATCHED` | Khuôn mặt không khớp |
| `LOW_CONFIDENCE` | Confidence thấp hơn threshold |
| `ERROR` | Lỗi xử lý |

#### Response 401 Unauthorized

```json
{
  "type": "https://ai-vision.campus.local/errors/unauthorized",
  "title": "Chưa xác thực",
  "status": 401,
  "detail": "Thiếu Bearer token"
}
```

---

### 2.6. GET /vision/models/info

**Mục đích:** Lấy thông tin chi tiết về model AI đang sử dụng.
**Auth:** Bearer token bắt buộc.
**Tested:** TC07.

#### Request

```
GET /vision/models/info
Authorization: Bearer <token>
```

#### Response 200 OK

```json
{
  "model_id": "yolov8n-v1.0",
  "model_type": "object_detection",
  "framework": "ultralytics",
  "framework_version": "8.3.0",
  "classes": [
    {"id": 0, "name": "person", "description": "Con người"},
    {"id": 2, "name": "car", "description": "Ô tô"}
  ],
  "confidence_threshold_default": 0.5,
  "input_size": 640,
  "accuracy_map": 0.73,
  "inference_time_ms_avg": 35,
  "last_updated": "2026-07-15T00:00:00Z",
  "status": "ACTIVE"
}
```

| Field | Kiểu | Ràng buộc |
|---|---|---|
| `model_id` | string | Bắt buộc |
| `model_type` | enum | object_detection, face_recognition, anomaly_detection |
| `framework` | string | Bắt buộc |
| `framework_version` | string | Bắt buộc |
| `classes[]` | array | Bắt buộc |
| `confidence_threshold_default` | number | 0.0-1.0 |
| `input_size` | integer | Bắt buộc |
| `accuracy_map` | number/null | 0.0-1.0 |
| `inference_time_ms_avg` | integer | Bắt buộc |
| `last_updated` | date-time | Bắt buộc |
| `status` | enum | ACTIVE, LOADING, ERROR, DEPRECATED |

---

## 3. Bảng tổng hợp error responses

Tất cả error responses tuân theo **RFC 9457 ProblemDetails**:

| Status | Tên | Trigger | Content-Type |
|---|---|---|---|
| `400` | BadRequest | Request không hợp lệ | `application/problem+json` |
| `401` | Unauthorized | Thiếu/sai token | `application/problem+json` |
| `404` | NotFound | Resource không tồn tại | `application/problem+json` |
| `408` | RequestTimeout | Xử lý quá lâu | `application/problem+json` |
| `413` | PayloadTooLarge | Payload > 10MB | `application/problem+json` |
| `422` | UnprocessableEntity | Validation fail | `application/problem+json` |
| `429` | TooManyRequests | Vượt rate limit | `application/problem+json` |
| `500` | InternalServerError | Lỗi server | `application/problem+json` |
| `503` | ServiceUnavailable | Service tạm nghỉ | `application/problem+json` |

---

## 4. Bảng test case

| # | Test ID | API | Method | Scenario | Input | Expected Status | Thực tế | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| 1 | TC01 | `/health` | GET | Service is alive | — | 200 | **PASS** | Health check |
| 2 | TC02 | `/vision/detect` | POST | Happy path `image_url` | body với `image_url` | 200 | **PASS** | Camera → Vision |
| 3 | TC03 | `/vision/detect` | POST | Happy path `image_base64` | body với `image_base64` | 200 | **PASS** | Binary input |
| 4 | TC04 | `/vision/detections/{id}` | GET | Get detection by ID | UUID hợp lệ từ TC02 | 200 | **PASS** | Store lookup |
| 5 | TC05 | `/vision/results/recent` | GET | Recent detections | query `limit=10` | 200 | **PASS** | Pagination |
| 6 | TC06 | `/vision/face-match` | POST | Face match happy path | `image_url`, `reference_image_url` | 200 | **PASS** | Core → Vision |
| 7 | TC07 | `/vision/models/info` | GET | Get model info | — | 200 | **PASS** | Model metadata |
| 8 | TC08 | `/vision/detections/{id}` | GET | Valid token + random UUID | UUID không tồn tại | 404 | **PASS** | Auth OK, not found |
| 9 | TC09 | `/vision/detect` | POST | Missing token | Không có `Authorization` | 401 | **PASS** | Auth fail |
| 10 | TC10 | `/vision/detect` | POST | Invalid token | `Bearer invalid-token` | 401 | **PASS** | Auth fail |
| 11 | TC11 | `/vision/detect` | POST | Missing `camera_id` | Không có `camera_id` | 422 | **PASS** | Validation |
| 12 | TC12 | `/vision/detect` | POST | Missing image input | Không có `image_url`/`image_base64` | 422 | **PASS** | Validation |
| 13 | TC13 | `/vision/detections/{id}` | GET | Invalid UUID format | `not-a-uuid` | 422 | **PASS** | UUID validation |
| 14 | TC14 | `/vision/detect` | POST | `confidence_threshold=1.0` | max boundary | 200 hoặc empty | **PASS** | Boundary |
| 15 | TC15 | `/vision/results/recent` | GET | `limit=100` (max) | max boundary | 200 | **PASS** | Boundary |

**Tổng kết:** 15/15 PASS trên cả **service thật** (`:8000`) và **Prism mock** (`:4011`).

---

## 5. Cách chạy test

### 5.1. Newman CLI (chính thức)

```bash
# Test trên Prism mock
npm run test:vision:mock

# Test trên service thật
npm run test:vision:local

# Test với data file (data-driven)
npm run test:vision:data

# CI: lint + mock test
npm run test:ci:vision
```

### 5.2. Postman Desktop

1. Import collection: `postman/collections/FIT4110_lab03_ai_vision.postman_collection.json`
2. Import environment: `postman/environments/FIT4110_lab03_ai_vision_mock.postman_environment.json` (mock) hoặc `_local` (service thật)
3. Chọn environment phù hợp
4. Bấm **Run** để chạy toàn bộ collection

### 5.3. Một số lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `ECONNREFUSED` | Service/Mock chưa chạy | Chạy `make serve-vision` hoặc `make mock-vision` |
| `401 Unauthorized` ở happy path | Sai hoặc thiếu token | Kiểm tra `{{authToken}}` trong environment |
| Test pass trên mock nhưng fail trên local | Service chưa đúng spec | Kiểm tra response với OpenAPI spec |
| `404 no path matched` trên Prism | Body không phải JSON hoặc Content-Type sai | Chọn `Body → raw → JSON` trong Postman |

---

## 6. Evidence (bằng chứng)

| File | Mô tả |
|---|---|
| `reports/vision-newman-report-mock.html` | HTML report — Prism mock |
| `reports/vision-newman-report-mock.xml` | JUnit XML — Prism mock |
| `reports/vision-newman-report-local.html` | HTML report — Service thật |
| `reports/vision-newman-report-local.xml` | JUnit XML — Service thật |
| `reports/contract-lint-vision.txt` | Spectral lint output |
| `docs/TEST_CASE.md` | Chi tiết kết quả từng test case |

---

## 7. Kết luận

✅ **6/6 endpoints đã kiểm thử** theo hợp đồng OpenAPI.
✅ **15/15 test cases PASS** trên cả service thật và Prism mock.
✅ **Tất cả response tuân thủ ProblemDetails** (RFC 9457).
✅ **Auth được kiểm chứng đúng cách** (không dùng `Prefer: code=401`).
✅ **Consumer-side smoke test** gọi được Camera Mock và Core Mock.
✅ **Hợp đồng OpenAPI lint pass** (0 error).

---

*Báo cáo kiểm thử API — FIT4110 Buổi 3 — team-vision — 2026-08-13*
