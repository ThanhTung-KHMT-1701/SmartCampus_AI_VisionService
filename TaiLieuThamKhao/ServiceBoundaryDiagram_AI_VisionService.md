# Service Boundary Diagram - AI Vision Service

## 1. Tổng quan Service

| Thuộc tính | Mô tả |
|------------|-------|
| **Tên Service** | AI Vision Service |
| **Mã đề tài** | Đề tài 4 |
| **Vai trò** | Xử lý hình ảnh bằng AI, phát hiện người, vật thể, người lạ trong khuôn viên trường |
| **Nhiệm vụ chính** | Nhận ảnh từ Camera Stream → Chạy mô hình AI → Trả về kết quả phát hiện |
| **Product** | Smart Campus Operations Platform |

---

## 2. Service Boundary Diagram

Sơ đồ tổng quan ranh giới service với 3 vùng chính:

**UPSTREAM (màu đỏ):** Camera Stream Service - Actor gọi AI Vision để phân tích ảnh

**INTERNAL (màu xanh dương):** Các thành phần bên trong AI Vision Service:
- API (POST /api/v1/detect) - Entry point nhận request
- Validator - Kiểm tra dữ liệu đầu vào
- Preprocessor - Tiền xử lý ảnh
- YOLOv8 Model - Mô hình AI phát hiện đối tượng
- Result Formatter - Định dạng kết quả
- Logger - Ghi log
- Redis Cache - Cache kết quả
- Health endpoint - Health check

**DOWNSTREAM (màu xanh lá):** Các service được AI Vision gọi:
- Core Business Service - Nhận kết quả phát hiện
- Analytics Service - Nhận metadata thống kê

**Luồng xử lý chính:**
1. Camera Stream gửi image_url, camera_id, timestamp đến API
2. API chuyển đến Validator kiểm tra
3. Nếu valid → Preprocessor xử lý → YOLOv8 phân tích
4. Kết quả định dạng và gửi đến Core Business và Analytics
5. Nếu invalid → Trả về 400 Bad Request

---

## 3. Sơ đồ Sequence (Happy Path & Error Path)

**Happy Path - Phát hiện thành công:**
1. Camera Stream gửi POST /api/v1/detect với {camera_id, image_url, timestamp}
2. API chuyển đến Validator kiểm tra schema và các trường
3. Validator xác nhận dữ liệu hợp lệ → chuyển đến Preprocessor
4. Preprocessor chuyển ảnh thành tensor → gửi đến YOLOv8 Model
5. Model trả về detections [{object, confidence, bbox}]
6. Result Formatter định dạng kết quả
7. Kết quả được gửi đến Core Business và Analytics
8. Core Business trả về 200 OK cho Camera Stream

**Error Path - Invalid request:**
1. Camera Stream gửi POST /api/v1/detect với dữ liệu không hợp lệ
2. API chuyển đến Validator
3. Validator trả về 422 Unprocessable Entity
4. API trả về 400 Bad Request cho Camera Stream

**Error Path - AI Model failed:**
1. Preprocessor gửi ảnh đến YOLOv8 Model
2. Model bị lỗi → trả về 500 Internal Server Error
3. API trả về 503 Service Unavailable cho Camera Stream

---

## 4. Luồng dữ liệu (Data Flow)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AI VISION SERVICE BOUNDARY                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   UPSTREAM ──────────────► INTERNAL ──────────────────────► DOWNSTREAM         │
│       │                        │                              │                  │
│   Camera ──────► API ────► Validator ────► YOLOv8 ──────► Core ───► Notif       │
│   Stream           │          │           │           Business ───► Alert       │
│       │            │          ▼           ▼               │                     │
│       │        Invalid    Preprocess    Detections        ▼                     │
│       │            │          │           │         Analytics                     │
│       ◀────────────┘          ▼           ▼               │                      │
│     400 Error         Result Formatter    │               ▼                      │
│                               │            │         Dashboard                    │
│                               ▼            ▼                                    │
│                          Redis Cache   Logs                                     │
│                               │                                                │
└───────────────────────────────┼────────────────────────────────────────────────┘
                                │
                          Monitoring
                          (Prometheus)
```

---

## 5. Contract Definition - Input/Output

### 5.1 Input Contract (Request)

AI Vision nhận request với các trường sau:

| Trường | Kiểu | Bắt buộc | Mô tả |
|---------|------|-----------|-------|
| camera_id | string | ✅ Có | ID của camera gửi ảnh |
| image_url | string (URL) | ✅ Có | URL của frame ảnh cần phân tích |
| timestamp | string (ISO8601) | ✅ Có | Thời điểm chụp ảnh |
| model_version | string | ❌ Không | Phiên bản model AI muốn sử dụng |

### 5.2 Output Contract (Response)

AI Vision trả về response chứa các trường sau:

| Trường | Kiểu | Mô tả |
|---------|------|--------|
| detection_id | string | ID duy nhất của phát hiện |
| detected | boolean | Có phát hiện đối tượng hay không |
| object | string | Loại đối tượng phát hiện (person, vehicle...) |
| confidence | float (0-1) | Độ tin cậy của kết quả |
| risk_level | enum | Mức độ rủi ro: low, medium, high |
| bbox | object | Tọa độ bounding box {x1, y1, x2, y2} |
| processing_time_ms | integer | Thời gian xử lý (mili-giây) |
| model_version | string | Phiên bản model đã sử dụng |
| timestamp | string | Thời điểm hoàn thành xử lý |

---

## 6. Ai gọi ai? (Upstream/Downstream Table)

### 6.1 Upstream - Ai gọi AI Vision?

| Actor/Service | Mục đích gọi | Endpoint | Format |
|---------------|--------------|----------|--------|
| **Camera Stream Service** | Gửi ảnh/frame để phân tích | `POST /api/v1/detect` | JSON |
| **Analytics Service** | Lấy thống kê phát hiện | `GET /api/v1/stats` | JSON |
| **Monitoring** | Health check | `GET /health` | JSON |

### 6.2 Downstream - AI Vision gọi ai?

| Service gọi | Mục đích | Action |
|-------------|----------|--------|
| **Core Business Service** | Gửi kết quả phát hiện để ra quyết định | HTTP POST callback |
| **Analytics Service** | Gửi metadata cho tổng hợp thống kê | HTTP POST /stats |
| **Redis Cache** | Cache kết quả phát hiện trùng lặp | Read/Write |
| **Prometheus/Grafana** | Export metrics | Pull metrics |

---

## 7. Bảng phân chia data ownership

| Data | Owner | Consumer | Retention |
|------|-------|----------|-----------|
| Detection logs | AI Vision | AI Vision, Analytics | 7 days |
| Image metadata | AI Vision | AI Vision | Session only |
| Camera config | Camera Stream | AI Vision (read) | N/A |
| Alert rules | Core Business | AI Vision (read) | N/A |

---

## 8. Error Handling Matrix

| Error Code | Nguyên nhân | Response | Xử lý downstream |
|------------|-------------|----------|-------------------|
| `400` | Invalid request body | `{error: "Invalid input", details: [...]}` | Không |
| `404` | Image URL not found | `{error: "Image not accessible"}` | Không |
| `422` | Schema validation failed | `{error: "Validation failed", fields: [...]}` | Không |
| `500` | AI model crashed | `{error: "Internal error"}` | Log to analytics |
| `503` | Service unavailable | `{error: "Service temporarily down"}` | Retry later |

---

## 9. Downstream Impact Assessment

Khi thay đổi API (version bump, field rename), các bước migration cần thực hiện:

1. **Notify consumers** - Thông báo cho các nhóm sử dụng API (Core Business, Analytics)
2. **Version bump** - Tăng version của API
3. **Update openapi.yaml** - Cập nhật specification
4. **Run integration tests** - Chạy test tích hợp để đảm bảo không có breaking change

---

## 10. Dependency Diagram

**Công nghệ sử dụng:**
- Python 3.11+ - Ngôn ngữ lập trình
- FastAPI - Web framework
- Ultralytics YOLOv8 - Thư viện object detection
- PyTorch - Deep learning backend
- Redis - Cache layer
- OpenCV - Xử lý ảnh
- Prometheus - Monitoring

**Luồng kết nối:**
- Camera Stream gửi request đến FastAPI Server qua POST /detect
- FastAPI Server giao tiếp với YOLOv8 Model
- YOLOv8 Model sử dụng PyTorch làm backend
- FastAPI Server sử dụng Redis Cache
- FastAPI Server export metrics đến Prometheus

**Kết nối với external services:**
- Camera Stream → FastAPI Server (gửi ảnh)
- FastAPI Server → Core Business (gửi kết quả phát hiện)
- FastAPI Server → Analytics (gửi metadata)

---

## 11. Endpoint Catalog Summary

| Method | Endpoint | Mô tả | Upstream/Downstream |
|--------|----------|-------|---------------------|
| `POST` | `/api/v1/detect` | Nhận ảnh, trả kết quả phát hiện | Camera Stream → AI Vision |
| `GET` | `/api/v1/detections` | Lấy lịch sử phát hiện | Analytics → AI Vision |
| `GET` | `/api/v1/stats` | Lấy thống kê phát hiện | Analytics → AI Vision |
| `GET` | `/health` | Health check | Monitoring → AI Vision |
| `GET` | `/ready` | Readiness check | Orchestrator → AI Vision |

---

## 12. Legend

| Symbol | Meaning |
|--------|---------|
| 🔴 | Upstream / Actor (gọi AI Vision) |
| 🟢 | Downstream / Consumer (AI Vision gọi) |
| 🔵 | Internal Service Component |
| 🟡 | AI/ML Component |
| 🟢 | Infrastructure/Cache |
| ➡️ | Sync call |
| -.- | Async/Callback |
| 🔴 Error | Error path |

---

## 13. Sample Request/Response

### 13.1 Sample Request

```json
POST /api/v1/detect
Content-Type: application/json

{
    "camera_id": "cam-gate-01",
    "image_url": "http://camera-stream:8000/frames/frame-001.jpg",
    "timestamp": "2026-08-04T09:10:00Z",
    "model_version": "yolov8n-v1.0"
}
```

### 13.2 Sample Response (Success)

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
    "detection_id": "det-uuid-12345",
    "detected": true,
    "object": "person",
    "confidence": 0.91,
    "risk_level": "medium",
    "bbox": {
        "x1": 150,
        "y1": 80,
        "x2": 300,
        "y2": 450
    },
    "processing_time_ms": 125,
    "model_version": "yolov8n-v1.0",
    "timestamp": "2026-08-04T09:10:01Z"
}
```

### 13.3 Sample Response (Error)

```json
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "error": "Invalid request",
    "code": "INVALID_INPUT",
    "message": "image_url must be a valid URL",
    "details": [
        {
            "field": "image_url",
            "message": "Invalid URL format"
        }
    ]
}
```

---

## 14. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-04 | AI Vision Team | Initial draft |
