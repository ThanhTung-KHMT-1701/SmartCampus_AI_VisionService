# FIT4110_Buoi04_Gateway — Docker Evidence

Ghi chép lại lý do thiết kế, các quyết định bảo mật, và kịch bản kiểm thử cho
stack Gateway. File này bổ sung cho `FIT4110_Buoi04_Docker/docs/docker-evidence.md`.

## 1. Động lực

Trong Lab04 (`FIT4110_Buoi04_Docker`), 3 service đều publish port ra host
(`8000`, `4012`, `4014`) và client phải biết 3 token khác nhau. Khi muốn
production-style, ta muốn:

1. **Che giấu cấu trúc nội bộ** — client chỉ biết 1 endpoint và 1 token.
2. **Giảm attack surface** — 3 service không lộ port ra Internet.
3. **Kiểm soát API exposure** — chỉ lộ một tập route nhất định, không phải
   toàn bộ OpenAPI của 3 service.
4. **Tái sử dụng image cũ** — không build lại 3 service.

## 2. Kiến trúc

```
                 ┌─────────────────────┐
   client ─────► │    api-gateway      │ ───► ai-vision:8000
   (token GW)    │     :8080          │ ───► core-business-mock:4012
                 └─────────────────────┘ ───► camera-stream-mock:4014
                            │
                       lab-net-gateway
                       (bridge, internal)
```

- Gateway là service duy nhất có `ports: 8080:8080` trong compose.
- 3 service hạ lưu **không** có block `ports:` — chỉ truy cập được từ trong
  `lab-net-gateway`.
- Client chỉ thấy cổng 8080 và route từ `src/gateway/routes.py`.

## 3. Bảo mật token

| Token | Phạm vi | Cách inject vào Gateway |
|---|---|---|
| `GATEWAY_AUTH_TOKEN` | Client ↔ Gateway | `.env` (đã `.gitignore`) → compose `environment` |
| `AI_VISION_AUTH_TOKEN` | Gateway ↔ ai-vision | compose `environment` của Gateway; **không** tới client |
| `CORE_AUTH_TOKEN` | Gateway ↔ core-business-mock | tương tự |
| `CAMERA_AUTH_TOKEN` | Gateway ↔ camera-stream-mock | tương tự |

Khi client gọi `POST /api/vision/detect`, Gateway:

1. Yêu cầu `Authorization: Bearer <GATEWAY_TOKEN>`.
2. Tự gắn `Authorization: Bearer <AI_VISION_AUTH_TOKEN>` khi gọi upstream.
3. `Body` và các header `Content-Type`/`Accept` được chuyển tiếp; loại bỏ
   hop-by-hop headers (`transfer-encoding`, `connection`, v.v.).

Token nội bộ được che qua hai lớp:

- Không có trong `Dockerfile` của Gateway (chỉ URL + port).
- Chỉ tồn tại trong `environment:` của compose và `.env` của host.

## 4. Bảng route curated

| Method | Gateway path | Method/Path upstream | Service |
|---|---|---|---|
| POST | `/api/vision/detect` | `POST /vision/detect` | ai-vision |
| POST | `/api/policies/evaluate-detection` | `POST /policies/evaluate-detection` | core-business-mock |
| GET  | `/api/cameras/{camera_id}/frames/latest` | `GET /cameras/{camera_id}/frames/latest` | camera-stream-mock |
| GET  | `/health` | (không proxy; local của Gateway) | self |
| GET  | `/health/services` | `GET /health` của 3 upstream (parallel) | all |
| GET  | `/routes` | (debug — liệt kê route đã đăng ký) | self |

Thêm/bớt route: chỉ sửa `ROUTE_TABLE` trong `src/gateway/routes.py`.

## 5. Kịch bản kiểm thử

```bash
# 5.1 Health của Gateway
curl -s http://localhost:8080/health | jq

# 5.2 Aggregate health của 3 upstream (parallel)
curl -s http://localhost:8080/health/services | jq

# 5.3 Liệt kê route
curl -s http://localhost:8080/routes | jq

# 5.4 Thiếu Bearer → 401
curl -s -X POST http://localhost:8080/api/vision/detect -i

# 5.5 Bearer sai → 401
curl -s -X POST http://localhost:8080/api/vision/detect \
  -H 'Authorization: Bearer wrong' -i

# 5.6 Vision detect hợp lệ → upstream trả 200, Gateway forward nguyên
curl -s -X POST http://localhost:8080/api/vision/detect \
  -H 'Authorization: Bearer local-dev-token-gateway' \
  -H 'Content-Type: application/json' \
  --data-binary '{"camera_id":"cam-gate-01","image_url":"http://storage.campus.local/images/frame-001.jpg","timestamp":"2026-08-22T10:00:00Z","confidence_threshold":0.6}' -i

# 5.7 Core evaluate → upstream trả 200 với alert_id
curl -s -X POST http://localhost:8080/api/policies/evaluate-detection \
  -H 'Authorization: Bearer local-dev-token-gateway' \
  -H 'Content-Type: application/json' \
  --data-binary '{"detection_id":"4fed4d9e-1acd-4ce5-93ad-cd87c73967d2","camera_id":"cam-gate-01","risk_level":"LOW","timestamp":"2026-08-22T02:08:25Z"}' -i

# 5.8 Camera latest frame (404 nếu không có frame)
curl -s http://localhost:8080/api/cameras/cam-gate-01/frames/latest \
  -H 'Authorization: Bearer local-dev-token-gateway' -i
```

## 6. Đã sẵn sàng cho bước tiếp theo

Sau khi stack chạy ổn định và kịch bản ở mục 5 đều pass, có thể:

- Thêm mới route chỉ bằng cách thêm vào `ROUTE_TABLE`.
- Chuyển sang `nginx`/`envoy`/`traefik` nếu cần load-balancing thật.
- Tách `httpx.AsyncClient` thành một connection pool riêng cho từng upstream
  (hiện tại dùng chung 1 client — đủ cho lab).

## 7. Bằng chứng thực nghiệm (2026-08-22)

Lần build/run đầu tiên trên host Windows 11 + Docker Engine, đã chạy và xác
nhận 11 tình huống (kết quả dưới đây là đã pass; stack đã được
`docker compose down` sau khi chạy xong).

### Build & boot

```
$ docker compose up -d --build
 Container fit4110-core-mock-lab04-gw Creating
 Container fit4110-ai-vision-lab04-gw Creating
 Container fit4110-camera-mock-lab04-gw Creating
 Container fit4110-api-gateway-lab04 Creating
 Container fit4110-camera-mock-lab04-gw Healthy
 Container fit4110-core-mock-lab04-gw Healthy
 Container fit4110-ai-vision-lab04-gw Healthy
 Container fit4110-api-gateway-lab04 Started

$ docker compose ps
NAME                           IMAGE                              STATUS                    PORTS
fit4110-ai-vision-lab04-gw     fit4110/ai-vision:lab04            Up (healthy)               8000/tcp
fit4110-api-gateway-lab04      fit4110/api-gateway:lab04          Up (healthy)               0.0.0.0:8080->8080/tcp
fit4110-camera-mock-lab04-gw   fit4110/camera-stream-mock:lab04   Up (healthy)               4014/tcp
fit4110-core-mock-lab04-gw     fit4110/core-business-mock:lab04   Up (healthy)               4012/tcp
```

Quan sát quan trọng: chỉ `api-gateway` có mapping port ra host
(`0.0.0.0:8080->8080`). Ba container còn lại chỉ có cổng nội bộ
(`8000/tcp`, `4012/tcp`, `4014/tcp`) — không lộ ra ngoài như yêu cầu.

### Smoke tests

| # | Request | Kỳ vọng | Thực tế | Pass? |
|---|---|---|---|---|
| 1 | `GET /health` | 200, body có `routesExposed` | 200, list đúng 3 route | ✅ |
| 2 | `GET /health/services` | 200, `services.*.status = up` | 200, cả 3 `up`, HTTP 200, latency 11–14 ms | ✅ |
| 3 | `GET /routes` | 200, đủ 3 entry | 200 | ✅ |
| 4 | `POST /api/vision/detect` (không Bearer) | 401 | 401 | ✅ |
| 5 | `POST /api/vision/detect` (Bearer sai) | 401 | 401 | ✅ |
| 6 | `POST /api/vision/detect` (đủ Bearer + body hợp lệ) | 200, có `detection_id` | 200, `75f8b348-b9b4-4ed4-970c-5d164b5633fd` | ✅ |
| 7 | `POST /api/policies/evaluate-detection` | 200, có `alert_id` | 200, `0341ce02-e442-4af8-b1fb-6d7e406c487e` | ✅ |
| 8 | `GET /api/cameras/cam-gate-01/frames/latest` (chưa ingest) | 404 | 404 (upstream không có frame) | ✅ |
| 9 | `POST /api/vision/detect` (thiếu `camera_id`) | 422 | 422 (validation từ ai-vision) | ✅ |
| 10 | `POST /api/vision/detect` (body không phải JSON) | 400 | 400 (gateway chặn trước khi forward) | ✅ |
| 11 | `GET /api/cameras/cam-library-02/frames/latest` | 404 | 404 (upstream không có frame cho camera) | ✅ |

### Lỗi đã phát hiện và sửa trong quá trình smoke-test

1. **`UnsupportedProtocol` trong `/health/services`** — `_probe()` truyền nhầm
   `"unused"` thay vì base URL vào `forward()`. Đã sửa thành `forward(base, …)`.

2. **`422 thay vì 401` cho route có path-param** — `lambda **kw` khiến FastAPI
   coi `**kw` là `**query` và validate query-string. Đã refactor handler về
   `request: Request` thuần, lấy path params từ `request.path_params`.

3. **`httpx` chuyển `json_body=None` cho GET** — `httpx.request(method="GET",
   json=None)` sẽ serialize `None` thành `b"null"` và gửi đi. Đã tách
   `json_body` ra khỏi kwargs khi method là GET.

Sau 3 fix trên, toàn bộ 11 test pass.

### Tear-down

```
$ docker compose down --remove-orphans
 Container fit4110-ai-vision-lab04-gw Removed
 Container fit4110-core-mock-lab04-gw Removed
 Container fit4110-camera-mock-lab04-gw Removed
 Network smartcampus-lab-net-gateway Removed

$ docker images --filter "reference=fit4110/*"
fit4110/api-gateway:lab04
fit4110/camera-stream-mock:lab04
fit4110/core-business-mock:lab04
fit4110/ai-vision:lab04
```

Image `fit4110/api-gateway:lab04` được giữ lại — tái sử dụng được cho lần
chạy sau (`docker compose up -d` không cần `--build`).
