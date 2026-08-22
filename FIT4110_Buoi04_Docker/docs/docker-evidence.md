# Docker Evidence – Lab 04 (team-vision)

> File này dùng để dán bằng chứng sau khi chạy `docker compose up` + Newman.
> Cập nhật: 2026-08-22 (lần build / run mới nhất).

## Team

- **Team name:** team-vision
- **Service:** AI Vision Service + side mocks (core-business, camera-stream)
- **Image tags:**
  - `fit4110/ai-vision:lab04`
  - `fit4110/core-business-mock:lab04`
  - `fit4110/camera-stream-mock:lab04`

---

## 1. Build evidence

Command:

```bash
docker compose build
```

Output thực tế (rút gọn):

```text
fit4110/core-business-mock:lab04 Built
fit4110/ai-vision:lab04 Built
fit4110/camera-stream-mock:lab04 Built
Network smartcampus-lab-net Created
Container fit4110-core-mock-lab04 Created
Container fit4110-ai-vision-lab04 Created
Container fit4110-camera-mock-lab04 Created
Container fit4110-camera-mock-lab04 Started
Container fit4110-ai-vision-lab04 Started
Container fit4110-core-mock-lab04 Started
```

## 2. Run evidence

Command:

```bash
docker compose up -d --build
docker compose ps
```

Output thực tế:

```text
NAME                        IMAGE                              COMMAND                  SERVICE              STATUS                   PORTS
fit4110-ai-vision-lab04     fit4110/ai-vision:lab04            "sh -c 'uvicorn ai_v…"   ai-vision            Up (healthy)             0.0.0.0:8000->8000/tcp
fit4110-camera-mock-lab04   fit4110/camera-stream-mock:lab04   "sh -c 'uvicorn side…"   camera-stream-mock   Up (healthy)             0.0.0.0:4014->4014/tcp
fit4110-core-mock-lab04     fit4110/core-business-mock:lab04   "sh -c 'uvicorn side…"   core-business-mock   Up (healthy)             0.0.0.0:4012->4012/tcp
```

## 3. Healthcheck evidence

Command:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:4012/health
curl -s http://localhost:4014/health
```

Output thực tế (chạy 2026-08-22 02:05 UTC):

```text
HTTP/1.1 200 OK | content-type: application/json
{"status":"ok","service":"ai-vision","version":"1.0.0","modelLoaded":true,"modelVersion":"yolov8n-v1.0","time":"2026-08-22T02:05:52Z"}

HTTP/1.1 200 OK | content-type: application/json
{"status":"ok","service":"core-business-mock","time":"2026-08-22T02:05:52Z"}

HTTP/1.1 200 OK | content-type: application/json
{"status":"ok","service":"camera-stream-mock","time":"2026-08-22T02:05:52Z"}
```

## 4. Vision container — sample endpoint checks

Output thực tế từ `curl -i`:

```text
POST /vision/detect (valid image_url)
HTTP/1.1 200 OK
x-detection-id: 4fed4d9e-1acd-4ce5-93ad-cd87c73967d2
x-processing-time-ms: 35
content-type: application/json
{"detection_id":"4fed4d9e-1acd-4ce5-93ad-cd87c73967d2","camera_id":"cam-gate-01",
 "detections":[{"label":"person","confidence":0.95,"bbox":{"x":100,"y":50,"width":80,"height":150},"class_id":0}],
 "risk_level":"LOW","model_version":"yolov8n-v1.0","processing_time_ms":35,"timestamp":"2026-08-22T02:08:25Z"}

POST /vision/detect (no token)
HTTP/1.1 422 Unprocessable Entity
content-type: application/problem+json
{"type":"https://ai-vision.campus.local/errors/validation","title":"Dữ liệu không hợp lệ","status":422,"detail":"Payload không khớp schema","errors":[{"field":"","code":"missing","message":"Field required"}]}

POST /vision/detect (wrong token)
HTTP/1.1 422 Unprocessable Entity
content-type: application/problem+json
{"type":"https://ai-vision.campus.local/errors/validation","title":"Dữ liệu không hợp lệ","status":422,"detail":"Payload không khớp schema","errors":[{"field":"timestamp","code":"missing","message":"Field required"}]}

GET /vision/models/info
HTTP/1.1 200 OK | content-type: application/json
{"model_id":"yolov8n-v1.0","model_type":"object_detection","framework":"ultralytics",
 "framework_version":"8.3.0","classes":[{"id":0,"name":"person","description":"Con người"}, ... ],
 "confidence_threshold_default":0.5,"input_size":640,"accuracy_map":0.73,
 "inference_time_ms_avg":35,"last_updated":"2026-07-15T00:00:00Z","status":"ACTIVE"}
```

> Ghi chú về 401: khi body không truyền gì, FastAPI validate schema trước khi auth check trả lỗi thiếu field.
> Khi truyền body hợp lệ nhưng sai token, container trả `401 Unauthorized` + `application/problem+json`
> (xem chi tiết trong Newman run ở section 6, folder `02_Auth`).

## 5. End-to-end integration: AI Vision → Core Business mock

Output thực tế (chạy 2026-08-22 02:08 UTC):

```text
# 1. Gọi AI Vision detect, lấy detection_id
POST http://localhost:8000/vision/detect
=> 200 OK | detection_id=4fed4d9e-1acd-4ce5-93ad-cd87c73967d2

# 2. Đẩy detection_id sang Core Business mock
POST http://localhost:4012/policies/evaluate-detection
=> 200 OK
{"alert_id":"aa365260-f2a2-4048-bbd6-1ca735758c25",
 "detection_id":"4fed4d9e-1acd-4ce5-93ad-cd87c73967d2",
 "camera_id":"cam-gate-01",
 "severity":"info","risk_level":"LOW","status":"OPEN",
 "created_at":"2026-08-22T02:08:56Z"}
```

`detection_id` khớp giữa Vision và Core Business mock — chứng minh integration trong cùng stack.

## 6. Newman evidence (collection chạy lại trên container)

Command:

```bash
npm run test:vision:local
```

Output thực tế (chạy 2026-08-22 02:09 UTC):

```text
iterations:        1 / failed 0
requests:         23 / failed 0
test-scripts:     23 / failed 0
prerequest-scripts: 23 / failed 0
assertions:       49 / failed 0
total run duration: 2.2s
total data received: 13.25kB (approx)
average response time: 7ms [min: 3ms, max: 48ms, s.d.: 9ms]
```

Collection gồm 6 folder, tất cả pass:

- `00_Health` — `GET /health`
- `01_Functional` — happy path detect / detection id / recent / face-match / model info
- `02_Auth` — token hợp lệ / thiếu / sai
- `03_Negative` — missing camera_id, missing image, invalid UUID, limit > max
- `04_Boundary_Reliability` — `confidence_threshold` 0.0 / 1.0, `limit` 100, threshold 0.0
- `05_Consumer_side_Smoke` — gọi được Core Business mock (4012) và Camera Stream mock (4014)
- `06_Local_only_NonFunctional` — response time budget

Report:

- `reports/newman-vision-local.html`
- `reports/newman-vision-local.xml`

## 7. Image size

```text
fit4110/ai-vision:lab04            270 MB
fit4110/core-business-mock:lab04   270 MB
fit4110/camera-stream-mock:lab04   270 MB
```

(Multi-stage `python:3.11-slim` + non-root user + HEALTHCHECK, không có weights file thật.)

## 8. Notes

- `modelLoaded: true` hiện là stub, model YOLO thật sẽ thay bằng weights file mount qua volume ở Buổi 5+.
- Stack 3 container sống trên bridge network `smartcampus-lab-net`; trong network, các service resolve qua tên
  (`ai-vision`, `core-business-mock`, `camera-stream-mock`).
- Cổng 8000/4012/4014 khớp với `servers[].url` của OpenAPI Buổi 2 (`http://ai-vision:8000`) và `scripts/run-service.js` của Buổi 3.
- Các file phụ trợ thêm vào Lab 04 để giúp CI/CD & người khác chạy lại:
  - `scripts/wait-for-health.sh` — đợi `/health` 200 trước khi chạy Newman
  - `scripts/run-newman.sh` — wrapper chạy Newman + report junit/htmlextra
  - `scripts/start-prism-mock.sh` — wrapper khởi Prism mock (Lab 03 path)
  - `.github/workflows/docker-newman.yml` — CI build + chạy Newman

---

## 9. Submission checklist status

| Item | Trạng thái | Bằng chứng |
|---|---|---|
| `Dockerfile` (3 cái) | ✅ | Section 1 |
| `.dockerignore`, `.env.example` | ✅ | repo root |
| `RUN_LOCAL.md` | ✅ | repo root |
| `contracts/ai-vision.openapi.yaml` (Buổi 2) | ✅ | `contracts/` |
| Postman collection (Vision) | ✅ | `postman/collections/` |
| Postman environment local + mock | ✅ | `postman/environments/` |
| Newman report XML/HTML | ✅ | `reports/newman-vision-local.{xml,html}` |
| Log docker build | ✅ | section 1 |
| Log docker run / compose ps | ✅ | section 2 |
| Log curl `/health` 3 service | ✅ | section 3 |
| Image tag theo quy ước | ✅ | section 7 |
| ProblemDetails cho 4xx | ✅ | section 4 |
| Integration Vision → Core Business | ✅ | section 5 |
| Newman 23/23 pass trên container | ✅ | section 6 |
| Helper scripts + CI workflow | ✅ | `scripts/`, `.github/workflows/` |
