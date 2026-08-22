# Docker Evidence – Lab 04 (team-vision)

> File này dùng để dán bằng chứng sau khi chạy `docker compose up` + Newman. Cập nhật sau mỗi lần build lại image.

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

Output (rút gọn):

```text
Image fit4110/core-business-mock:lab04 Built
Image fit4110/ai-vision:lab04 Built
Image fit4110/camera-stream-mock:lab04 Built
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
NAME                        IMAGE                              COMMAND                  SERVICE              CREATED          STATUS                   PORTS
fit4110-ai-vision-lab04     fit4110/ai-vision:lab04            "sh -c 'uvicorn ai_v…"   ai-vision            7 minutes ago     Up 7 minutes (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
fit4110-camera-mock-lab04   fit4110/camera-stream-mock:lab04   "sh -c 'uvicorn side…"   camera-stream-mock   7 minutes ago     Up 7 minutes (healthy)   0.0.0.0:4014->4014/tcp, [::]:4014->4014/tcp
fit4110-core-mock-lab04     fit4110/core-business-mock:lab04   "sh -c 'uvicorn side…"   core-business-mock   7 minutes ago     Up 7 minutes (healthy)   0.0.0.0:4012->4012/tcp, [::]:4012->4012/tcp
```

## 3. Healthcheck evidence

Command:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:4012/health
curl -s http://localhost:4014/health
```

Output thực tế:

```text
HTTP/1.1 200 OK | content-type: application/json
{"status":"ok","service":"ai-vision","version":"1.0.0","modelLoaded":true,"modelVersion":"yolov8n-v1.0","time":"2026-08-22T01:13:10Z"}

HTTP/1.1 200 OK | content-type: application/json
{"status":"ok","service":"core-business-mock","time":"2026-08-22T01:13:10Z"}

HTTP/1.1 200 OK | content-type: application/json
{"status":"ok","service":"camera-stream-mock","time":"2026-08-22T01:13:10Z"}
```

## 4. Vision container — sample endpoint checks

```text
POST /vision/detect (valid image_url)
HTTP/1.1 200 OK
x-detection-id: 9955aea1-4e11-46b0-a89e-606d1ec00996
x-processing-time-ms: 35

POST /vision/detect (no token)
HTTP/1.1 401 Unauthorized
content-type: application/problem+json
{"type":"https://ai-vision.campus.local/errors/401","title":"Thiếu Bearer token","status":401,"detail":"Thiếu Bearer token"}

POST /vision/detect (missing image_url/base64)
HTTP/1.1 422 Unprocessable Entity
content-type: application/problem+json
{"type":"https://ai-vision.campus.local/errors/422","title":"Phải cung cấp image_url hoặc image_base64 (mutually exclusive)","status":422,"detail":"..."}

GET /vision/models/info
HTTP/1.1 200 OK | content-type: application/json
{"model_id":"yolov8n-v1.0","model_type":"object_detection","framework":"ultralytics",...}
```

## 5. End-to-end integration: AI Vision → Core Business mock

```text
# 1. Gọi AI Vision detect, lấy detection_id
POST http://localhost:8000/vision/detect
=> 200 OK | detection_id=9955aea1-4e11-46b0-a89e-606d1ec00996

# 2. Đẩy detection_id sang Core Business mock
POST http://localhost:4012/policies/evaluate-detection
=> 200 OK
{"alert_id":"8f2f4a05-...","detection_id":"9955aea1-...","camera_id":"cam-gate-01",
 "severity":"high","risk_level":"HIGH","status":"OPEN","created_at":"2026-08-22T01:18:59Z"}

# 3. Đẩy frame sang Camera Stream mock
POST http://localhost:4014/frames
=> 201 Created
```

## 6. Newman evidence (collection chạy lại trên container)

Command:

```bash
npm run test:vision:local
```

Output:

```text
iterations:    1 / failed 0
requests:     23 / failed 0
assertions:   49 / failed 0
total run duration: 2.1s
average response time: 7ms [min: 3ms, max: 42ms, s.d.: 7ms]
```

Collection bao gồm 6 folder:

- `01_Functional`
- `02_Auth`
- `03_Negative`
- `04_Boundary_Reliability`
- `05_Consumer_side_Smoke` — gọi được Core Business mock (4012) và Camera Stream mock (4014) → chứng minh AI Vision kết nối ngang được với side mock trong cùng stack
- `06_Local_only_NonFunctional`

Report:

- `reports/newman-vision-local.html` (~474 KB)
- `reports/newman-vision-local.xml` (~12 KB)

## 7. Image size

```text
fit4110/ai-vision          lab04   ~270 MB
fit4110/core-business-mock lab04   ~270 MB
fit4110/camera-stream-mock lab04   ~270 MB
```

(Multi-stage `python:3.11-slim` + non-root user + HEALTHCHECK, không có weights file thật.)

## 8. Notes

- `modelLoaded: true` hiện là stub, model YOLO thật sẽ thay bằng weights file mount qua volume ở Buổi 5+.
- Stack 3 container sống trên bridge network `smartcampus-lab-net`; trong network, các service resolve qua tên (`ai-vision`, `core-business-mock`, `camera-stream-mock`).
- Cổng 8000/4012/4014 khớp với `servers[].url` của OpenAPI Buổi 2 (`http://ai-vision:8000`) và `scripts/run-service.js` của Buổi 3.

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
