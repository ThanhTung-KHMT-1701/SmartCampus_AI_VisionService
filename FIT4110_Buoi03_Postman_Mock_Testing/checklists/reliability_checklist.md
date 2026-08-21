# Reliability Checklist — Team Vision (AI Vision)

## 1. Functional tests

- [x] Có test cho endpoint health (GET /health).
- [x] Có test happy path cho endpoint chính (POST /vision/detect với image_url).
- [x] Có test happy path với image_base64 (POST /vision/detect).
- [x] Có kiểm tra status code 2xx (200 cho tất cả endpoint).
- [x] Có kiểm tra field quan trọng trong response (detection_id, camera_id, detections, model_version).
- [x] Có ít nhất 1 test đọc dữ liệu danh sách (GET /vision/results/recent) và chi tiết (GET /vision/detections/{id}).
- [x] Có test cho face match (POST /vision/face-match).
- [x] Có test cho model info (GET /vision/models/info).

## 2. Auth tests

- [x] Có test thiếu token (POST /vision/detect no Authorization header).
- [x] Có test sai token (POST /vision/detect với Bearer invalid-token-xyz).
- [x] Endpoint public được khai báo rõ (GET /health có security: []).
- [x] Test thể hiện đúng expected status (skip trên mock, 401/403 khi chạy local).
- [x] Auth test KHÔNG dùng Prefer: code=401.

## 3. Negative tests

- [x] Có test thiếu field bắt buộc (thiếu camera_id).
- [x] Có test thiếu image input (thiếu cả image_url và image_base64).
- [x] Có test sai kiểu dữ liệu (UUID invalid cho detectionId).
- [x] Có test sai enum hoặc giá trị ngoài miền (limit=999 > max 100).
- [x] Lỗi trả về theo cùng một error model (ProblemDetails của RFC 9457).

## 4. Boundary tests

- [x] Có test min/max (confidence_threshold = 0.0 và 1.0).
- [x] Có test limit/pagination (limit=100 bound max).
- [x] Có test face match threshold boundary (0.0).
- [x] Có ghi chú kỳ vọng xử lý dữ liệu biên trong README/test-case-matrix.

## 5. Reliability tests cơ bản

- [x] Có kiểm tra response time (POST /vision/detect < 5000ms, GET /health < 500ms).
- [x] Có mô tả timeout mong muốn (request-timeout 408 documented).
- [x] Có test hoặc ghi chú retry/idempotency (idempotency key trong header tùy chọn).
- [x] Có consumer-side smoke test với mock của team-core (alerts/recent) và team-camera (frames).

## 6. Evidence

- [x] Collection export JSON: `postman/collections/FIT4110_lab03_ai_vision.postman_collection.json`.
- [x] Environment mock export JSON: `postman/environments/FIT4110_lab03_ai_vision_mock.postman_environment.json`.
- [x] Environment local export JSON: `postman/environments/FIT4110_lab03_ai_vision_local.postman_environment.json`.
- [x] Newman report XML/HTML: `reports/vision-newman-report-mock.{xml,html}`.
- [x] Test-case matrix đã điền: `test-case-matrix.csv`.
- [x] Biên bản handshake đã điền: `consumer-provider-handshake.md`.

## 7. Pattern tuân thủ (Lab 03 yêu cầu)

- [x] Không hardcode `baseUrl`, `authToken` - tất cả qua environment variables.
- [x] Không dùng `Prefer: code=401` để chứng minh auth thật.
- [x] Boundary test kiểm response từ server, không kiểm request body.
- [x] Consumer-side test gọi mock của nhóm khác (Core Business, Camera Stream), không gọi lại API của chính mình.
- [x] Latency test chỉ chạy trên local environment.

## 8. Mock chạy cùng nhau

- [x] AI Vision mock: port 4011.
- [x] IoT mock (provider cho consumer smoke): port 4010.
- [x] Core Business mock: port 4012 ✅ (src/side_mocks/core_business.py, chạy `npm run serve:core-mock`)
- [x] Camera Stream mock: port 4014 ✅ (src/side_mocks/camera_stream.py, chạy `npm run serve:camera-mock`)
