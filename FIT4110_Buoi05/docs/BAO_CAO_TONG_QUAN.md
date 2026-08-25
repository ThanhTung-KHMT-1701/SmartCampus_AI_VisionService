# BÁO CÁO TỔNG QUAN — AI Vision Docker Service
## FIT4110 Buổi 5 — Smart Campus Operations Platform

**Service:** AI Vision Service (Dockerized)
**Container image:** `fit4110/ai-vision:lab05`
**Port exposed:** `8000`
**Ngày:** 2026-08-25

---

## 1. Tổng quan hệ thống

### 1.1. Vị trí của AI Vision trong Smart Campus

AI Vision Service nằm ở trung tâm của hệ thống Smart Campus, đóng vai trò **vừa là Provider vừa là Consumer**:

```
┌──────────────────────────────────────────────────────────────────────┐
│                    SMART CAMPUS OPERATIONS PLATFORM                    │
│                                                                      │
│  ┌──────────────┐     ┌────────────────┐     ┌──────────────────┐   │
│  │ Camera Stream│────▶│  AI Vision     │────▶│  Core Business   │   │
│  │  (Consumer)  │     │  (Provider)   │     │  (Consumer)      │   │
│  │              │◀────│  (Consumer)   │◀────│  (Provider)      │   │
│  └──────────────┘     └────────────────┘     └──────────────────┘   │
│         ▲                    │                       │                 │
│         │                    │                       │                 │
│         │              ┌─────┴─────┐            ┌────┴────┐         │
│         └──────────────▶│   IoT     │◀───────────│Notifica-│         │
│                        │Ingestion  │            │  tion   │         │
│                        └───────────┘            └─────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2. Điểm khác biệt so với Buổi 3

| Khía cạnh | Buổi 3 (Mock) | Buổi 5 (Docker) |
|---|---|---|
| AI Vision chạy ở đâu | Prism mock (:4011) | Docker container (:8000) |
| Inference engine | Static JSON stub | Python FastAPI + in-memory store |
| Auth middleware | Không mock được | **Thật** — từ chối token sai |
| Validation | Prism chọn response theo contract | **Thật** — FastAPI Pydantic validation |
| Camera/Core mocks | Side mocks trong cùng repo | **Chạy ngoài host** ở LAN IP |
| Mục đích | Consumer gọi provider mock | Consumer gọi **service thật** |

---

## 2. Kiến trúc Buổi 5

### 2.1. Sơ đồ kiến trúc

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MÁY HOST (Windows)                                                     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Docker Desktop                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │  Container: fit4110-ai-vision-lab05                         │ │   │
│  │  │  Image: fit4110/ai-vision:lab05                            │ │   │
│  │  │  Port: 8000:8000 (host:container)                         │ │   │
│  │  │                                                              │ │   │
│  │  │  FastAPI AI Vision Service (Python 3.11)                   │ │   │
│  │  │    ├── /health              (public)                       │ │   │
│  │  │    ├── /vision/detect      (POST, auth required)           │ │   │
│  │  │    ├── /vision/detections/{id}  (GET, auth required)       │ │   │
│  │  │    ├── /vision/results/recent    (GET, auth required)      │ │   │
│  │  │    ├── /vision/face-match        (POST, auth required)     │ │   │
│  │  │    └── /vision/models/info       (GET, auth required)      │ │   │
│  │  │                                                              │ │   │
│  │  │  In-Memory DetectionStore (max 1000 records)               │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  External Services (NOT in Docker)                               │   │
│  │                                                                   │   │
│  │  Camera Stream Mock:  http://192.168.137.115:8001                │   │
│  │  Core Business Mock:   http://192.168.137.79:8001                │   │
│  │                                                                   │   │
│  │  (AI Vision gọi được qua LAN, nhưng hiện tại chưa dùng)        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Postman Client                                                   │   │
│  │  ├── Collection: FIT4110_lab05_ai_vision_real                    │   │
│  │  ├── Env Docker Local: baseUrl=http://localhost:8000             │   │
│  │  └── Env LAN Remote:  baseUrl=http://192.168.137.XXX:8000         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2. Cổng và service mapping

| Cổng | Service | Môi trường | Mục đích |
|---|---|---|---|
| `:8000` | AI Vision Service | **Docker container** | Service thật — inference, face-match |
| `:192.168.137.115:8001` | Camera Stream Mock | Host (LAN) | Consumer-side smoke test |
| `:192.168.137.79:8001` | Core Business Mock | Host (LAN) | Forward-compatibility |

---

## 3. Luồng dữ liệu

### 3.1. Luồng 1 — Camera Stream gọi AI Vision Docker

```
Bước 1: Camera Stream chụp frame từ camera vật lý
         ↓
Bước 2: Camera Stream gửi frame đến AI Vision Docker
         POST http://localhost:8000/vision/detect
         Header: Authorization: Bearer local-dev-token-vision
         Body: {
           "camera_id": "cam-lab05-gate",
           "image_url": "http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest",
           "timestamp": "2026-08-25T08:00:00Z",
           "confidence_threshold": 0.6
         }
         ↓
Bước 3: AI Vision (Docker) nhận frame, chạy stub inference
         - Phát hiện đối tượng: person, car, truck...
         - Tính confidence score
         - Gán risk_level: LOW / MEDIUM / HIGH / CRITICAL
         ↓
Bước 4: AI Vision trả kết quả cho Camera Stream
         200 OK
         Headers: X-Detection-Id, X-Processing-Time-Ms
         Body: {
           "detection_id": "uuid-của-detection",
           "camera_id": "cam-lab05-gate",
           "detections": [
             {"label": "person", "confidence": 0.95, "bbox": {...}, "class_id": 0}
           ],
           "risk_level": "LOW",
           "model_version": "yolov8n-v1.0",
           "processing_time_ms": 45,
           "timestamp": "2026-08-25T08:00:01Z"
         }
```

### 3.2. Luồng 2 — Consumer-side smoke test

```
Test: AI Vision Docker gọi Camera Stream Mock (chạy ngoài Docker)
      GET http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest
      Header: Authorization: Bearer lab-token-camera
      ↓ Camera Stream mock trả frame gần nhất
```

---

## 4. Auth Token

| Service | Token | Cổng |
|---|---|---|
| AI Vision Docker | `local-dev-token-vision` | :8000 |
| Camera Stream Mock | `lab-token-camera` | 192.168.137.115:8001 |
| Core Business Mock | `lab-token-core` | 192.168.137.79:8001 |

---

## 5. Cấu trúc project Buổi 5

```
FIT4110_Buoi05/
├── src/                          ← Service code (đóng gói vào Docker)
│   └── ai_vision_service/
│       ├── main.py                ← FastAPI app
│       ├── schemas.py             ← Pydantic models
│       └── store.py               ← In-memory detection store
├── postman/
│   ├── collections/
│   │   └── FIT4110_lab05_ai_vision_real.postman_collection.json
│   └── environments/
│       ├── FIT4110_lab05_docker_local.postman_environment.json
│       └── FIT4110_lab05_lan_remote.postman_environment.json
├── scripts/
│   ├── contract-smoke.ps1        ← 15 requests nhanh (Invoke-WebRequest)
│   ├── run-18-test-cases.ps1     ← 18 test cases + evidence per case
│   └── collect-evidence.ps1      ← Newman HTML/JUnit report
├── mock-data/
│   ├── vision-detect-valid.json
│   ├── vision-detect-base64-valid.json
│   ├── vision-detect-missing-image.json
│   ├── vision-detect-both-images.json
│   ├── vision-detect-boundary-low.json
│   ├── vision-detect-boundary-high.json
│   ├── face-match-valid.json
│   ├── face-match-high-threshold.json
│   ├── vision-detect-invalid-camera-id.json
│   └── camera-frame-valid.json
├── reports/
│   ├── README.md
│   ├── vision-newman-report-docker-latest.html
│   ├── vision-newman-report-docker-latest.xml
│   └── evidence/                   ← stdout/body cho từng test case
├── docs/
│   ├── BAO_CAO_TONG_QUAN.md       ← (file này)
│   ├── BAO_CAO_API.md
│   └── HUONG_DAN_CHAY_TESTS.md
├── consumer-provider-handshake.md  ← Contract handshake record
├── test-case-matrix.csv           ← Matrix 18 test cases
├── .gitignore
├── Dockerfile                      ← Multi-stage build
├── docker-compose.yml              ← Chỉ chạy AI Vision
├── requirements.txt                ← Python dependencies
├── .env.example                   ← Cấu hình mẫu
└── README.md                      ← Hướng dẫn build/run
```

---

## 6. Kết quả kiểm thử dự kiến

| Nhóm test | Số request | Mục đích |
|---|---|---|
| 00_Health | 1 | Verify service alive |
| 01_Functional | 6 | Happy paths trên service thật |
| 02_Auth | 4 | Auth thật (Docker enforcement) |
| 03_Negative | 7 | Validation thật (Pydantic) |
| 04_Boundary | 4 | Edge values |
| 05_Consumer | 2 | Consumer-side smoke (LAN) |
| 06_Local | 3 | Performance SLA (Docker) |
| **Tổng** | **27** | |

---

*Báo cáo tổng quan — FIT4110 Buổi 5 — 2026-08-25*
