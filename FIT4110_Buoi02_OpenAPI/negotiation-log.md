# Biên bản đàm phán hợp đồng API

- Cặp đàm phán: Pair 01 (Camera Stream → AI Vision) và Pair 02 (Core Business → AI Vision)
- Product: A
- Provider: AI Vision Service (A4)
- Consumer: Camera Stream (A2), Core Business (A6)
- Phiên: v1.0
- Ngày: 2026-08-11

---

## Issue #1

- **Raised by**: Consumer (Camera Stream)
- **Endpoint**: `POST /vision/detect`
- **Concern**: Camera Stream muốn gửi ảnh dạng multipart/form-data thay vì JSON body để tránh vấn đề với ảnh lớn và encoding.
- **Proposal**: Hỗ trợ cả hai cách: JSON body (image_url/image_base64) và multipart/form-data (file upload).
- **Resolution**: Modified
- **Rationale**: AI Vision chấp nhận hỗ trợ cả hai cách. Tuy nhiên, để đơn giản hóa MVP, chỉ support JSON body trước. Multipart có thể thêm sau khi cần. Consumer có thể dùng `image_url` để reference ảnh đã upload sẵn.
- **Impact**: MVP chỉ support JSON body. Multipart được đưa vào backlog để discuss sau.

---

## Issue #2

- **Raised by**: Provider (AI Vision)
- **Endpoint**: `POST /vision/detect`
- **Concern**: AI Vision cần biết rõ format của `timestamp`. Nếu Camera gửi timestamp không đúng ISO8601, validation sẽ fail.
- **Proposal**: Thống nhất timestamp phải là ISO8601 format. AI Vision sẽ trả 400 nếu format sai.
- **Resolution**: Accepted
- **Rationale**: ISO8601 là standard và được hỗ trợ tốt bởi mọi ngôn ngữ/libraries. Đảm bảo consistency giữa các services.
- **Impact**: Camera Stream cần format timestamp đúng ISO8601 trước khi gửi request.

---

## Issue #3

- **Raised by**: Consumer (Core Business)
- **Endpoint**: `POST /vision/face-match`
- **Concern**: Core Business cần biết khi nào face match không chắc chắn - nên trả 200 với status LOW_CONFIDENCE hay trả 422?
- **Proposal**: Core Business đề xuất trả 422 khi confidence gần ngưỡng (ví dụ: 0.68-0.75) để Consumer biết cần xử lý đặc biệt.
- **Resolution**: Modified
- **Rationale**: AI Vision chọn trả 200 với status LOW_CONFIDENCE thay vì 422. Lý do: 422 thường dùng cho request không hợp lệ về nghiệp vụ, nhưng request này hoàn toàn hợp lệ - chỉ là kết quả không đủ tin cậy. Consumer nên xử lý LOW_CONFIDENCE trong business logic.
- **Impact**: Core Business cần handle thêm case LOW_CONFIDENCE trong business logic, không phải như lỗi.

---

## Issue #4

- **Raised by**: Consumer (Camera Stream)
- **Endpoint**: `GET /vision/results/recent`
- **Concern**: Camera Stream cần filter results theo thời gian và camera_id. Hiện tại API không support filter.
- **Proposal**: Thêm query parameters `camera_id`, `from_time`, `to_time` để filter kết quả.
- **Resolution**: Accepted
- **Rationale**: Filtering là requirement hợp lý cho use case tổng hợp dữ liệu. AI Vision thêm các query parameters này vào endpoint.
- **Impact**: API được mở rộng với optional query parameters. Backward compatible vì các parameters đều optional.

---

## Issue #5

- **Raised by**: Provider (AI Vision)
- **Endpoint**: `POST /vision/detect`, `POST /vision/face-match`
- **Concern**: AI Vision cần implement idempotency để tránh xử lý trùng lặp khi Consumer retry request.
- **Proposal**: AI Vision đề xuất dùng header `X-Idempotency-Key` để identify duplicate requests. Nếu key đã được xử lý, trả kết quả đã lưu.
- **Resolution**: Modified
- **Rationale**: Consumer (Camera Stream và Core Business) đồng ý idempotency là useful nhưng không muốn implement phức tạp ở MVP. Kết luận: MVP không support idempotency key. Implement sau nếu cần. Consumer sẽ handle retry bằng cách kiểm tra detection_id trong response.
- **Impact**: MVP không có idempotency. Consumer cần handle retry cẩn thận để tránh duplicate detection.

---

## Issue #6

- **Raised by**: Consumer (Core Business)
- **Endpoint**: `POST /vision/detect`, `POST /vision/face-match`
- **Concern**: Core Business cần `trace_id` để correlate logs giữa Camera Stream → AI Vision → Core Business → Notification.
- **Proposal**: Core Business đề xuất thêm `trace_id` field vào request body và response body.
- **Resolution**: Accepted
- **Rationale**: Trace ID là standard practice cho distributed tracing. AI Vision sẽ:
  - Accept `trace_id` trong request body (optional)
  - Echo `trace_id` trong response body (hoặc trả null nếu không được gửi)
  - Log `trace_id` trong internal logs để debug
- **Impact**: API được mở rộng với optional `trace_id` field. Backward compatible.

---

## Issue #7

- **Raised by**: Consumer (Camera Stream)
- **Endpoint**: `POST /vision/detect`
- **Concern**: Camera muốn biết rõ timeout expectation. Nếu AI Vision xử lý quá lâu, Camera nên chờ hay cancel?
- **Proposal**: AI Vision đề xuất timeout 30 giây. Nếu vượt quá, trả 408 Request Timeout.
- **Resolution**: Accepted
- **Rationale**: 30 giây là reasonable timeout cho image processing. Camera Stream sẽ set client-side timeout tương ứng và implement retry với exponential backoff.
- **Impact**: Camera Stream cần implement timeout handling ở client side. AI Vision sẽ trả 408 nếu timeout xảy ra.

---

## Issue #8

- **Raised by**: Consumer (Core Business)
- **Endpoint**: `GET /vision/detections/{detectionId}`
- **Concern**: Core Business cần biết detection results được lưu trong bao lâu để biết khi nào truy vấn sẽ bị 404.
- **Proposal**: AI Vision thống nhất: Detection results được cache trong memory tối đa 24 giờ. Sau đó sẽ trả 404.
- **Resolution**: Accepted
- **Rationale**: 24 giờ là balance giữa storage/resource và usability. Analytics có thể dùng `/vision/results/recent` để lấy data mà không phụ thuộc vào individual detection IDs.
- **Impact**: Core Business nên cache/persist detection results nếu cần refer lâu dài. Không nên rely on AI Vision storage.

---

# Chốt hợp đồng v1.0

Provider sign-off: **[AI Vision Team - A4]**  
Consumer sign-off: **[Camera Stream Team - A2]**  
Consumer sign-off: **[Core Business Team - A6]**  
Witness (GV/TA): ________________________  
Date: 2026-08-11

---

## Ghi chú warning nếu Spectral còn cảnh báo

| Warning | Lý do chấp nhận tạm thời | Kế hoạch sửa |
|---|---|---|
| Không có | Tất cả warnings đã được xử lý | Không cần |

---

## Tóm tắt các quyết định quan trọng

1. **Chỉ support JSON body** cho MVP, multipart/form-data để sau
2. **Timestamp format**: ISO8601 bắt buộc
3. **Face match LOW_CONFIDENCE**: Trả 200 với status LOW_CONFIDENCE, không phải 422
4. **Filtering**: Thêm query params `camera_id`, `from_time`, `to_time`
5. **Idempotency**: Không support ở MVP
6. **Trace ID**: Optional field, được echo trong response
7. **Timeout**: 30 giây, trả 408 nếu vượt quá
8. **Storage duration**: Detection results cache 24 giờ

---

## API Endpoints được chốt

| Method | Path | Mô tả | Consumer |
|---|---|---|---|
| GET | `/health` | Health check | All |
| POST | `/vision/detect` | Phát hiện đối tượng | Camera Stream |
| GET | `/vision/detections/{detectionId}` | Lấy detection theo ID | All |
| GET | `/vision/results/recent` | Lấy detections gần đây | Core Business, Analytics |
| POST | `/vision/face-match` | So khớp khuôn mặt | Core Business |
| GET | `/vision/models/info` | Thông tin model AI | Monitoring |
