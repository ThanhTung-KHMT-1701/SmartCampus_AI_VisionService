# BÁO CÁO TỔNG QUAN — AI Vision Service
## FIT4110 Buổi 3 — Smart Campus Operations Platform

**Team:** team-vision
**Service:** AI Vision Service
**Hợp đồng:** `contracts/ai-vision.openapi.yaml`
**Ngày:** 2026-08-13

---

## 1. Tổng quan hệ thống

### 1.1. Vị trí của AI Vision trong Smart Campus

AI Vision Service nằm ở trung tâm của hệ thống Smart Campus, đóng vai trò **vừa là Provider vừa là Consumer**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SMART CAMPUS OPERATIONS PLATFORM                  │
│                                                                     │
│  ┌──────────────┐     ┌────────────────┐     ┌──────────────────┐  │
│  │ Camera Stream│────▶│  AI Vision     │────▶│  Core Business   │  │
│  │  (Consumer)  │     │  (Provider)   │     │  (Consumer)      │  │
│  │              │◀────│  (Consumer)   │◀────│  (Provider)      │  │
│  └──────────────┘     └────────────────┘     └──────────────────┘  │
│         ▲                    │                       │                │
│         │                    │                       │                │
│         │              ┌─────┴─────┐            ┌────┴────┐          │
│         │              │   IoT     │            │Notifica-│          │
│         └──────────────▶│Ingestion  │◀───────────│  tion   │          │
│                        │(Provider) │            │(Consumer│          │
│                        └───────────┘            └─────────┘          │
│                                                                     │
│  ┌──────────────┐                                                    │
│  │  Analytics   │◀──────── các service gọi analytics để lấy metric  │
│  │  (Consumer)  │                                                    │
│  └──────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2. Vai trò của AI Vision

| Vai trò | Service tương ứng | Cổng | Mô tả |
|---|---|---|---|
| **Provider** (cung cấp API) | AI Vision Service | :8000 (thật) / :4011 (Prism mock) | Trả kết quả detection, face-match, model info |
| **Consumer** (gọi service khác) | Camera Stream | :4014 (mock) | AI Vision gọi `/cameras/{id}/frames/latest` để lấy frame |
| **Consumer** (gọi service khác) | Core Business | :4012 (mock) | AI Vision gọi `/alerts/recent`, `/policies/evaluate-detection` |

---

## 2. Luồng đi của dữ liệu

### 2.1. Luồng 1 — Camera Stream gọi AI Vision (Pair 01)

```
Bước 1: Camera Stream chụp frame từ camera vật lý
         ↓
Bước 2: Camera Stream gửi frame (image_url hoặc base64) đến AI Vision
         POST http://localhost:4011/vision/detect
         Header: Authorization: Bearer <token>
         Body: {
           "camera_id": "cam-gate-01",
           "image_url": "http://storage.campus.local/images/frame-001.jpg",
           "timestamp": "2026-08-13T07:30:00Z",
           "confidence_threshold": 0.6
         }
         ↓
Bước 3: AI Vision nhận frame, chạy inference (YOLO model)
         - Phát hiện đối tượng: person, car, truck...
         - Tính confidence score
         - Gán risk_level: LOW / MEDIUM / HIGH / CRITICAL
         ↓
Bước 4: AI Vision trả kết quả cho Camera Stream
         200 OK
         Headers: X-Detection-Id, X-Processing-Time-Ms
         Body: {
           "detection_id": "uuid-của-detection",
           "camera_id": "cam-gate-01",
           "detections": [
             {"label": "person", "confidence": 0.95, "bbox": {...}, "class_id": 0}
           ],
           "risk_level": "LOW",
           "model_version": "yolov8n-v1.0",
           "processing_time_ms": 45,
           "timestamp": "2026-08-13T07:30:01Z"
         }
         ↓
Bước 5: Camera Stream lưu detection_id để truy vấn sau
```

### 2.2. Luồng 2 — Core Business gọi AI Vision để xác minh khuôn mặt (Pair 02)

```
Bước 1: Core Business nhận yêu cầu xác minh sinh viên
         (ví dụ: sinh viên quẹt thẻ tại cổng)
         ↓
Bước 2: Core Business gọi AI Vision để so khớp khuôn mặt
         POST http://localhost:4011/vision/face-match
         Header: Authorization: Bearer <token>
         Body: {
           "image_url": "http://storage.campus.local/images/face-detected.jpg",
           "reference_image_url": "http://storage.campus.local/profiles/student-001.jpg",
           "threshold": 0.75,
           "trace_id": "trace-20260813-001",
           "timestamp": "2026-08-13T07:30:00Z"
         }
         ↓
Bước 3: AI Vision chạy face matching (FaceNet model)
         - So sánh 2 ảnh
         - Tính confidence score
         - So sánh với threshold
         ↓
Bước 4: AI Vision trả kết quả
         200 OK
         Header: X-Trace-Id
         Body: {
           "match_id": "uuid-của-match",
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
         ↓
Bước 5: Core Business quyết định hành động
         - matched=true → cho phép vào
         - matched=false → từ chối
```

### 2.3. Luồng 3 — Core Business tổng hợp detection để tạo alert

```
Bước 1: Core Business gọi AI Vision lấy danh sách detection gần đây
         GET http://localhost:4011/vision/results/recent?limit=20&camera_id=cam-gate-01
         Header: Authorization: Bearer <token>
         ↓
Bước 2: AI Vision trả danh sách
         200 OK
         Body: {
           "items": [...],
           "nextCursor": null,
           "hasMore": false
         }
         ↓
Bước 3: Core Business phân tích risk_level
         - MEDIUM/HIGH/CRITICAL → tạo alert
         POST http://localhost:4012/policies/evaluate-detection
         Body: {
           "detection_id": "uuid",
           "camera_id": "cam-gate-01",
           "risk_level": "HIGH",
           "timestamp": "..."
         }
         ↓
Bước 4: Alert được gửi đến Notification service
```

### 2.4. Luồng 4 — Consumer-side smoke test (AI Vision gọi mock của service khác)

AI Vision không trực tiếp gọi Camera Stream hay Core Business trong business logic, nhưng **consumer-side smoke test** xác nhận AI Vision có thể gọi được các service phụ thuộc:

```
Test 1: AI Vision gọi Camera Stream mock (lấy frame mới nhất)
        GET http://localhost:4014/cameras/cam-gate-01/frames/latest
        Header: Authorization: Bearer <token>
        ↓ Camera Stream mock trả frame gần nhất

Test 2: AI Vision gọi Core Business mock (lấy alert gần đây)
        GET http://localhost:4012/alerts/recent?limit=5
        Header: Authorization: Bearer <token>
        ↓ Core Business mock trả danh sách alert
```

---

## 3. Kiến trúc dữ liệu

### 3.1. Detection Data Flow

```
Camera Stream                    AI Vision Service              In-Memory Store
     │                                │                              │
     │──── POST /vision/detect ──────▶│                              │
     │   image_url: frame URL         │                              │
     │   camera_id: cam-gate-01       │── inference (YOLO stub) ─────▶│
     │                                │                              │
     │                                │◀── detection_id (UUID) ───────│
     │                                │    stored: {                 │
     │◀── 200 OK ─────────────────────│      detection_id,            │
     │   detection_id: uuid-abc        │      camera_id,               │
     │   detections: [...],            │      detections[],            │
     │   risk_level: LOW              │      risk_level               │
     │                                │    }                         │
     │                                │                              │
     │──── GET /vision/detections/    │                              │
     │       {uuid-abc} ─────────────▶│                              │
     │                                │◀── lookup ────────────────────│
     │◀── 200 OK (full record) ──────│                              │
```

### 3.2. Face Match Data Flow

```
Core Business                   AI Vision Service              FaceNet Model
     │                                │                              │
     │──── POST /vision/face-match ──▶│                              │
     │   image_url                    │                              │
     │   reference_image_url          │── compare faces ─────────────▶│
     │   threshold: 0.75              │                              │
     │                                │◀── confidence: 0.93 ──────────│
     │                                │    matched: true             │
     │◀── 200 OK ─────────────────────│                              │
     │   match_id: uuid-def           │                              │
     │   matched: true                │                              │
     │   status: MATCHED              │                              │
```

---

## 4. Cách chạy các Service

### 4.1. Sơ đồ các cổng (ports)

| Cổng | Service | Môi trường | Mục đích |
|---|---|---|---|
| `:8000` | AI Vision Service (FastAPI) | Local | Service thật, chạy inference |
| `:4010` | Prism Mock IoT | Mock | Mock theo OpenAPI IoT |
| `:4011` | Prism Mock AI Vision | Mock | Mock theo OpenAPI AI Vision |
| `:4012` | Core Business Mock (Python) | Mock | Consumer-side smoke |
| `:4014` | Camera Stream Mock (Python) | Mock | Consumer-side smoke |

### 4.2. Chuẩn bị môi trường

```bash
# 1. Kích hoạt conda environment (đã có đủ Python, FastAPI, uvicorn)
conda activate DichVuKetNoi

# 2. Cài dependencies Node.js
cd FIT4110_Buoi03_Postman_Mock_Testing
npm install
```

### 4.3. Cách 1: Dùng Make (đơn giản nhất)

```bash
# Chạy AI Vision service thật
make serve-vision           # → http://localhost:8000

# Chạy Prism mock AI Vision
make mock-vision           # → http://localhost:4011

# Chạy Camera Stream mock (cho consumer-side smoke)
make serve-camera-mock      # → http://localhost:4014

# Chạy Core Business mock (cho consumer-side smoke)
make serve-core-mock        # → http://localhost:4012

# Chạy tất cả cùng lúc (service thật + 2 side-mock)
make serve-vision
make serve-camera-mock
make serve-core-mock

# Chạy Prism mock cả IoT + Vision
make mock-all
```

### 4.4. Cách 2: Dùng npm script

```bash
# AI Vision service thật (FastAPI + uvicorn)
npm run serve:vision

# Prism mock AI Vision
npm run mock:vision

# Camera Stream mock
npm run serve:camera-mock

# Core Business mock
npm run serve:core-mock
```

### 4.5. Cách 3: Chạy Python trực tiếp

```bash
# AI Vision service thật
python -m src.ai_vision_service.main
# → http://localhost:8000

# Camera Stream mock
python -m src.side_mocks.camera_stream
# → http://localhost:4014

# Core Business mock
python -m src.side_mocks.core_business
# → http://localhost:4012
```

### 4.6. Kiểm tra service đã chạy

```bash
# Health check từng service
curl http://localhost:8000/health        # AI Vision thật
curl http://localhost:4011/health        # Prism mock AI Vision
curl http://localhost:4014/health        # Camera Stream mock
curl http://localhost:4012/health        # Core Business mock
```

### 4.7. Chạy test bằng Newman CLI

```bash
# Test trên Prism mock (:4011)
npm run test:vision:mock

# Test trên service thật (:8000)
npm run test:vision:local

# Test trên cả 2 môi trường (CI pattern)
npm run lint:vision && npm run test:vision:mock
```

### 4.8. Lint hợp đồng OpenAPI

```bash
# Lint contract AI Vision
npm run lint:vision

# Lint tất cả contracts
npm run lint:contracts
```

---

## 5. Auth Token

| Service | Token | Cổng |
|---|---|---|
| AI Vision thật | `local-dev-token-vision` | :8000 |
| Prism mock AI Vision | `lab-token-vision` | :4011 |
| Camera Stream mock | `lab-token-camera` | :4014 |
| Core Business mock | `lab-token-core` | :4012 |

Sử dụng header: `Authorization: Bearer <token>`

---

## 6. Cấu trúc project

```
FIT4110_Buoi03_Postman_Mock_Testing/
├── contracts/
│   ├── ai-vision.openapi.yaml       ← Hợp đồng AI Vision
│   └── iot-ingestion.openapi.yaml   ← Hợp đồng IoT (tham khảo)
├── postman/
│   ├── collections/
│   │   └── FIT4110_lab03_ai_vision.postman_collection.json
│   └── environments/
│       ├── FIT4110_lab03_ai_vision_mock.postman_environment.json
│       └── FIT4110_lab03_ai_vision_local.postman_environment.json
├── src/
│   ├── ai_vision_service/
│   │   ├── main.py                 ← AI Vision service thật (FastAPI)
│   │   ├── schemas.py              ← Pydantic models
│   │   └── store.py                ← In-memory detection store
│   └── side_mocks/
│       ├── camera_stream.py        ← Camera Stream mock (Python FastAPI)
│       └── core_business.py        ← Core Business mock (Python FastAPI)
├── reports/
│   ├── vision-newman-report-mock.html
│   ├── vision-newman-report-local.html
│   └── contract-lint-vision.txt
├── docs/
│   ├── TEST_CASE.md                ← Báo cáo test case đã chạy
│   ├── CONSUMER_SIDE_TESTING.md
│   └── GITHUB_ACTIONS_GUIDE.md
├── checklists/
│   ├── reliability_checklist.md
│   └── submission_checklist.md
├── templates/
│   ├── test-case-matrix.csv
│   └── consumer-provider-handshake.md
└── Makefile                        ← Lệnh chạy nhanh tất cả
```

---

## 7. Tóm tắt luồng dữ liệu

```
┌──────────────────────────────────────────────────────────────────────┐
│                     LUỒNG DỮ LIỆU CHÍNH                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [Camera] ──frame URL──▶ [Vision] ──detection──▶ [Core]             │
│     │                    │                          │                │
│     │                    │                          ▼                │
│     │                    │                    [Alert/Notification]   │
│     ▼                    ▼                          │                │
│  [AI Vision] ◀──face── [Core]                          │            │
│     │                   (khớp khuôn mặt để xác minh)   │            │
│     │                                                     ▼         │
│     └────────────── consumer-side smoke ──────────── [IoT, Analytics] │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Kết quả kiểm thử:** 23 requests, 49 assertions, **0 fail** trên cả service thật và Prism mock.

---

*Báo cáo tổng quan — FIT4110 Buổi 3 — team-vision — 2026-08-13*
