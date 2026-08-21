# TEAM TASKS — Gợi ý test case theo 7 service

Mỗi nhóm có thể dùng bảng này để nhanh chóng tạo test-case matrix.

---

## 1. team-iot — IoT Ingestion

Endpoint gợi ý:

- `POST /readings`
- `GET /readings/latest`
- `GET /devices/{id}/readings`
- `GET /health`

Test bắt buộc:

- Happy path tạo reading thành công.
- Thiếu `device_id` → 400.
- Sai `metric` ngoài enum → 400.
- Không có token → 401.
- Boundary value: nhiệt độ quá cao / quá thấp.
- Latest readings có `items` là array.
- Response time dưới ngưỡng.

---

## 2. team-camera — Camera Stream

Endpoint gợi ý:

- `POST /frames`
- `POST /frames/{id}/analyze`
- `GET /cameras/{id}/frames/latest`
- `GET /health`

Test bắt buộc:

- Upload frame hợp lệ.
- Sai `camera_id`.
- `image_url` không hợp lệ.
- Trigger analyze gọi mock AI Vision.
- AI Vision trả 503 thì Camera xử lý lỗi lịch sự.
- Boundary: frame quá lớn / thiếu metadata.

---

## 3. team-gate — Access Gate

Endpoint gợi ý:

- `POST /access-events`
- `GET /access-events`
- `GET /cards/{id}`
- `POST /cards`
- `GET /health`

Test bắt buộc:

- Gửi sự kiện quẹt thẻ hợp lệ.
- Card không tồn tại.
- Sai `gate_id`.
- Không có token.
- Kiểm tra allow/deny.
- Consumer smoke với Core Business mock.

---

## 4. team-vision — AI Vision

Endpoint gợi ý:

- `POST /detect`
- `GET /detections/{id}`
- `GET /models/info`
- `GET /health`

Test bắt buộc:

- Detect từ `image_url`.
- Detect từ base64.
- Sai định dạng ảnh.
- Confidence nằm trong [0,1].
- Model info cacheable.
- Consumer smoke cho Camera và Core.

---

## 5. team-analytics — Analytics

Endpoint gợi ý:

- `POST /events`
- `GET /metrics/daily`
- `GET /metrics/access`
- `GET /metrics/alerts`
- `GET /health`

Test bắt buộc:

- Ingest event từ IoT.
- Ingest event từ Core.
- Query metric theo khoảng thời gian.
- Thiếu `from`/`to`.
- `from > to` → 400.
- Consumer smoke với mock IoT/Core.

---

## 6. team-core — Core Business

Endpoint gợi ý:

- `POST /policies/evaluate-sensor`
- `POST /policies/evaluate-access`
- `POST /policies/evaluate-detection`
- `GET /alerts`
- `POST /policies`
- `GET /health`

Test bắt buộc:

- Evaluate sensor vượt ngưỡng tạo warning/alert.
- Evaluate access allow/deny.
- Evaluate detection person/unknown.
- Policy không tồn tại.
- Sai schema.
- Provider smoke cho Notification.

---

## 7. team-notify — Notification

Endpoint gợi ý:

- `POST /notifications`
- `GET /notifications/{id}`
- `GET /notifications`
- `POST /notifications/{id}/retry`
- `GET /health`

Test bắt buộc:

- Gửi notification hợp lệ.
- Sai channel.
- Thiếu recipient.
- Retry notification failed.
- Dedupe cùng `alert_id`.
- Consumer smoke với Core mock.
