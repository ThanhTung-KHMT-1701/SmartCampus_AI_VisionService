# 📬 SmartCampus AI Vision API - Postman Testing Suite

Bộ test API hoàn chỉnh cho **AI Vision Service** sử dụng Postman và Newman CLI.

---

## 📋 Tổng Quan

### Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────┐
│                   Internet / LAN                    │
│                                                      │
│                  Port 8000 (Public)                 │
│                        ↓                            │
│              ┌─────────────────────┐                │
│              │  AI Vision Gateway  │                │
│              │   (Authentication)  │                │
│              └──────────┬──────────┘                │
│                         │                           │
└─────────────────────────┼───────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         │    ai_vision-net (Internal)    │
         │                                 │
         │   ┌──────────────┐  ┌────────┐ │
         │   │  AI Engine   │  │ MySQL  │ │
         │   │  (Port 9000) │  │ (3306) │ │
         │   └──────────────┘  └────────┘ │
         └─────────────────────────────────┘
```

### Endpoints Coverage

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/health` | ❌ | Kiểm tra service health |
| POST | `/vision/detect` | ✅ | Phát hiện đối tượng trong ảnh |
| POST | `/vision/face-match` | ✅ | So khớp khuôn mặt |
| GET | `/vision/detections/{id}` | ✅ | Lấy detection theo ID |
| GET | `/vision/results/recent` | ✅ | Danh sách detections gần đây |
| GET | `/vision/models/info` | ✅ | Thông tin model AI |

---

## 📦 Files Structure

```
postman/
├── collections/
│   └── SmartCampus_AI_Vision_Complete.postman_collection.json
├── environments/
│   └── SmartCampus_AI_Vision.postman_environment.json
└── README.md (this file)
```

---

## 🚀 Quick Start

### 1. Import vào Postman Desktop

1. Mở **Postman Desktop**
2. Click **Import** → **File**
3. Chọn file:
   - `collections/SmartCampus_AI_Vision_Complete.postman_collection.json`
   - `environments/SmartCampus_AI_Vision.postman_environment.json`
4. Chọn environment **SmartCampus AI Vision Environment** ở góc phải trên
5. Click vào collection và chạy từng request

### 2. Chạy với Newman CLI

#### Cài đặt Newman

```bash
# Cài Newman globally
npm install -g newman

# Cài Newman HTML reporter
npm install -g newman-reporter-htmlextra
```

#### Chạy toàn bộ tests

```bash
# Di chuyển vào thư mục postman
cd FIT4110_Buoi05_GPU/postman

# Chạy với HTML report
newman run collections/SmartCampus_AI_Vision_Complete.postman_collection.json \
  -e environments/SmartCampus_AI_Vision.postman_environment.json \
  -r htmlextra,json,cli \
  --reporter-htmlextra-export ../reports/newman-report.html \
  --reporter-json-export ../reports/newman-report.json \
  --timeout-request 60000 \
  --delay-request 1000
```

#### Windows PowerShell

```powershell
newman run collections/SmartCampus_AI_Vision_Complete.postman_collection.json -e environments/SmartCampus_AI_Vision.postman_environment.json -r htmlextra,json,cli --reporter-htmlextra-export ..\reports\newman-report.html --reporter-json-export ..\reports\newman-report.json --timeout-request 60000 --delay-request 1000
```

---

## 🔐 Authentication

### Bearer Token

Tất cả endpoints (trừ `/health`) yêu cầu **Bearer Token** trong header:

```http
Authorization: Bearer smartcampus-vision-2026-secure-token
```

Token được lưu trong environment variable `{{authToken}}`.

### Thay đổi Token

Chỉnh sửa file `environments/SmartCampus_AI_Vision.postman_environment.json`:

```json
{
  "key": "authToken",
  "value": "your-new-token-here",
  "type": "secret"
}
```

Hoặc trong Postman Desktop: **Environments** → Click vào environment → Edit `authToken`.

---

## 📝 Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `baseUrl` | `http://localhost:8000` | Gateway API base URL |
| `authToken` | `smartcampus-vision-2026-secure-token` | Bearer token |
| `cameraId` | `cam-gate-01` | Camera ID mẫu |
| `testImageUrl` | `https://picsum.photos/640/480?random=1` | URL ảnh test |
| `testFaceUrl1` | `https://picsum.photos/300/300?random=face1` | URL ảnh khuôn mặt 1 |
| `testFaceUrl2` | `https://picsum.photos/400/400?random=face2` | URL ảnh khuôn mặt 2 |
| `detectionId` | _(auto-saved)_ | Detection ID từ response |
| `nextCursor` | _(auto-saved)_ | Pagination cursor |
| `matchId` | _(auto-saved)_ | Face match ID |

---

## 🧪 Test Scenarios

### 1. Health Check (1 test)

- ✅ **GET Health - Service OK**: Kiểm tra service đang chạy

### 2. Object Detection (4 tests)

- ✅ **POST Detect - Valid Image URL**: Detection thành công với image URL
- ❌ **POST Detect - Missing Auth Token**: 401 khi không có token
- ❌ **POST Detect - Invalid Camera ID Format**: 422 khi camera_id sai format
- ❌ **POST Detect - Missing Required Fields**: 422 khi thiếu fields bắt buộc

### 3. Face Matching (2 tests)

- ✅ **POST Face Match - Valid Request**: Face matching thành công
- ❌ **POST Face Match - Missing Reference Image**: 422 khi thiếu reference image

### 4. Detection Results (4 tests)

- ✅ **GET Recent Detections - Default Limit**: Lấy danh sách detections
- ✅ **GET Recent Detections - With Camera Filter**: Filter theo camera_id
- ✅ **GET Detection by ID**: Lấy detection cụ thể bằng ID
- ❌ **GET Detection by ID - Not Found**: 404 khi ID không tồn tại

### 5. Model Info (1 test)

- ✅ **GET Model Info**: Lấy thông tin YOLO model

**Tổng cộng: 12 test cases**

---

## 🎯 Expected Responses

### Success Response (200 OK)

#### Detection Response

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
  "timestamp": "2026-08-27T05:30:01Z"
}
```

#### Face Match Response

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
  "timestamp": "2026-08-27T05:30:02Z"
}
```

### Error Response (RFC 9457)

```json
{
  "type": "https://smartcampus.edu.vn/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "camera_id must match pattern ^[a-z0-9-]+$",
  "instance": "/vision/detect",
  "errors": [
    {
      "field": "camera_id",
      "message": "string_pattern_mismatch"
    }
  ]
}
```

---

## 🔧 Troubleshooting

### 1. Connection Refused (ECONNREFUSED)

**Lỗi**: `Error: connect ECONNREFUSED 127.0.0.1:8000`

**Giải pháp**:
```bash
# Kiểm tra Gateway có đang chạy không
docker ps | findstr smartcampus-ai-vision-gateway

# Nếu không chạy, start lại
cd FIT4110_Buoi05_GPU
docker-compose up -d
```

### 2. Request Timeout

**Lỗi**: `Error: Request timeout after 30000ms`

**Giải pháp**:
- Tăng timeout trong Newman: `--timeout-request 60000`
- Kiểm tra AI Engine: `docker logs smartcampus-ai-inference-engine`

### 3. 401 Unauthorized

**Lỗi**: `Status: 401 Unauthorized`

**Giải pháp**:
- Kiểm tra `authToken` trong environment
- Đảm bảo token khớp với `.env`: `AI_VISION_AUTH_TOKEN`

### 4. 422 Validation Error

**Lỗi**: `camera_id must match pattern ^[a-z0-9-]+$`

**Giải pháp**:
- Camera ID chỉ được dùng: `a-z`, `0-9`, `-`
- Ví dụ hợp lệ: `cam-gate-01`, `cam-library-02`
- Ví dụ SAI: `CAM_01`, `Cam-Gate-01`

### 5. Model Not Loaded

**Lỗi**: `503 Service Unavailable - Model not loaded`

**Giải pháp**:
```bash
# Kiểm tra AI Engine logs
docker logs smartcampus-ai-inference-engine

# Chờ model download xong (6.2MB)
# Kiểm tra health endpoint
curl http://localhost:8000/health
```

---

## 📊 Newman Reports

Sau khi chạy Newman, reports được lưu tại:

```
FIT4110_Buoi05_GPU/reports/
├── newman-report.html          # Interactive HTML report
├── newman-report.json          # Raw JSON results
└── TEST_SUMMARY.md             # Human-readable summary
```

### Mở HTML Report

**Windows**:
```powershell
start ..\reports\newman-report.html
```

**Linux/Mac**:
```bash
open ../reports/newman-report.html
```

---

## 🎨 API Contract Compliance

Postman collection này tuân thủ 100% với:

- ✅ **OpenAPI Spec**: `FIT4110_Buoi02_OpenAPI/openapi.yaml`
- ✅ **Spectral Rules**: `FIT4110_Buoi02_OpenAPI/campus-spectral.yaml`
- ✅ **RFC 9457**: Problem Details for HTTP APIs
- ✅ **Snake Case**: Tất cả fields dùng `snake_case` (camera_id, image_url, timestamp)
- ✅ **ISO 8601**: Timestamps theo chuẩn ISO 8601
- ✅ **UUID v7**: Detection IDs theo format UUIDv7

---

## 📚 Additional Resources

### OpenAPI Spec
```bash
# View OpenAPI spec
cat ../FIT4110_Buoi02_OpenAPI/openapi.yaml

# Validate với Spectral
npx @stoplight/spectral-cli lint ../FIT4110_Buoi02_OpenAPI/openapi.yaml
```

### Docker Commands
```bash
# Xem logs Gateway
docker logs -f smartcampus-ai-vision-gateway

# Xem logs AI Engine
docker logs -f smartcampus-ai-inference-engine

# Kiểm tra health của tất cả services
docker-compose ps
```

### Manual API Testing
```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Select-Object -ExpandProperty Content

# Object detection
$body = @{
    camera_id = "cam-gate-01"
    image_url = "https://picsum.photos/640/480"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer smartcampus-vision-2026-secure-token"
    "Content-Type" = "application/json"
}

Invoke-WebRequest -Uri "http://localhost:8000/vision/detect" -Method POST -Body $body -Headers $headers -UseBasicParsing | Select-Object -ExpandProperty Content
```

---

## 🤝 Contributing

Nếu cần thêm test cases:

1. Mở Postman Desktop
2. Import collection
3. Thêm request mới vào folder tương ứng
4. Viết test scripts trong tab **Tests**
5. Export collection: **Collection** → **⋮** → **Export** → **Collection v2.1**
6. Replace file `collections/SmartCampus_AI_Vision_Complete.postman_collection.json`

---

## 📞 Support

- **OpenAPI Spec**: `FIT4110_Buoi02_OpenAPI/openapi.yaml`
- **Docker Logs**: `docker logs smartcampus-ai-vision-gateway`
- **Newman Docs**: https://www.npmjs.com/package/newman
- **Postman Docs**: https://learning.postman.com/

---

**Updated**: 2026-08-27  
**Version**: 1.0.0  
**Maintainer**: AI Vision Team (A4/B4)
