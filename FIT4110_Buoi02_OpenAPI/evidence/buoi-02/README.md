# Evidence - Buổi 02 OpenAPI Contract

## Tóm tắt

Buổi 02 tập trung vào việc thiết kế và đàm phán hợp đồng API cho AI Vision Service.

---

## 1. Spectral Lint Report

Spectral lint đã pass với **0 errors**.

File: `spectral-report.txt`

### Command:
```bash
spectral lint openapi.yaml --ruleset campus-spectral.yaml
```

### Kết quả:
```
No results with a severity of 'error' found!
```

---

## 2. API Endpoints được chốt

AI Vision Service cung cấp **6 endpoints** cho 2 cặp đàm phán:

### Pair 01: Camera Stream → AI Vision (REST sync)

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Kiểm tra trạng thái service |
| POST | `/vision/detect` | Phát hiện đối tượng trong ảnh |
| GET | `/vision/detections/{detectionId}` | Lấy kết quả detection theo ID |
| GET | `/vision/models/info` | Lấy thông tin model AI |

### Pair 02: Core Business → AI Vision (REST sync)

| Method | Path | Mô tả |
|---|---|---|
| POST | `/vision/face-match` | So khớp khuôn mặt |
| GET | `/vision/results/recent` | Lấy danh sách detections gần đây |

---

## 3. Negotiation Log Summary

Đã đàm phán và giải quyết **8 issues**:

1. **Issue #1**: Multipart/form-data vs JSON body - Chỉ support JSON cho MVP
2. **Issue #2**: Timestamp format - ISO8601 bắt buộc
3. **Issue #3**: Face match LOW_CONFIDENCE - Trả 200 với status LOW_CONFIDENCE
4. **Issue #4**: Filtering - Thêm query params `camera_id`, `from_time`, `to_time`
5. **Issue #5**: Idempotency - Không support ở MVP
6. **Issue #6**: Trace ID - Optional field
7. **Issue #7**: Timeout - 30 giây, trả 408
8. **Issue #8**: Storage duration - Cache 24 giờ

---

## 4. Mock Server Test Commands

### Prerequisites

```bash
npm run install:cli
npm run mock
```

### Test Commands

```bash
# Test 1: Health check
curl -i http://localhost:4010/health

# Test 2: Detect objects
curl -i -X POST http://localhost:4010/vision/detect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "camera_id": "cam-gate-01",
    "image_url": "http://storage.campus.local/images/test.jpg",
    "timestamp": "2026-08-11T10:30:00Z"
  }'

# Test 3: Get detection by ID
curl -i http://localhost:4010/vision/detections/0196fb3d-4ad7-7d1e-9f49-5d5148d2babc \
  -H "Authorization: Bearer test-token"

# Test 4: Face match
curl -i -X POST http://localhost:4010/vision/face-match \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "image_url": "http://storage.campus.local/images/face.jpg",
    "reference_image_url": "http://storage.campus.local/profiles/student-001.jpg",
    "threshold": 0.75,
    "timestamp": "2026-08-11T10:30:00Z"
  }'

# Test 5: Get recent detections
curl -i "http://localhost:4010/vision/results/recent?limit=10" \
  -H "Authorization: Bearer test-token"
```

---

## 5. API Features

### Required OpenAPI 3.1.0 features đã implement:

- [x] OpenAPI 3.1.0 format
- [x] Schema đặt trong `components/schemas` với `$ref`
- [x] Union type với `null` (VD: `type: [string, 'null']`)
- [x] `oneOf` + `discriminator` (trong CampusEvent của template, AI Vision dùng `anyOf`)
- [x] Problem Details cho error responses
- [x] Examples cho mỗi endpoint
- [x] Tags để nhóm API
- [x] OperationId cho mỗi operation

---

## 6. Screenshots

Screenshot của mock server test sẽ được lưu trong thư mục `mock-screenshots/`.

---

## 7. Files bàn giao

| File | Mô tả | Trạng thái |
|---|---|---|
| `openapi.yaml` | Hợp đồng API đầy đủ | Hoàn thành |
| `docs/analysis-provider.md` | Phân tích từ góc nhìn Provider | Hoàn thành |
| `docs/analysis-consumer.md` | Phân tích từ góc nhìn Consumer | Hoàn thành |
| `negotiation-log.md` | Biên bản đàm phán với 8 issues | Hoàn thành |
| `VERSIONING.md` | Chính sách versioning API | Hoàn thành |
| `evidence/buoi-02/spectral-report.txt` | Spectral lint report | Hoàn thành |

---

## 8. Sign-off

**Provider**: AI Vision Team (A4)  
**Consumer 1**: Camera Stream Team (A2)  
**Consumer 2**: Core Business Team (A6)  
**Date**: 2026-08-11
