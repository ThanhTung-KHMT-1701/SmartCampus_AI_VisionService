# Phân tích yêu cầu — vai Consumer

- Cặp đàm phán: 02 — Core Business ↔ AI Vision
- Product: A / B — Smart Campus Operations Platform
- Consumer service: Core Business (A6/B6)
- Provider service: AI Vision (A4/B4)
- Người viết: [Tên thành viên Core Business]
- Ngày: [YYYY-MM-DD]

---

## 1. Resource Consumer cần nhận/gửi

| Resource | Consumer dùng để làm gì? | Field bắt buộc với Consumer | Field có thể tùy chọn |
|---|---|---|---|
| FaceMatchResult | Ra quyết định nghiệp vụ (mở cổng, tạo alert) | matchId, status, confidence, timestamp | personId (null khi NO_MATCH) |
| Detection | Lưu log audit cho từng phân tích ảnh | detectionId, status, confidence, traceId | — |
| VisionResultPage | Liệt kê kết quả gần đây để kiểm tra/audit | items, nextCursor, hasMore | — |

## 2. API Consumer cần gọi

| Method | Path | Lúc nào gọi? | Kỳ vọng response |
|---|---|---|---|
| POST | `/vision/face-match` | Khi có frame/embedding cần xác minh danh tính | 200 + FaceMatchResult |
| GET | `/vision/detections/{detectionId}` | Tra cứu chi tiết một detection theo id | 200 + Detection |
| GET | `/vision/detections` | Liệt kê detection theo trạng thái (cursor) | 200 + DetectionPage |
| GET | `/vision/results/recent` | Audit/kiểm tra các kết quả gần đây | 200 + VisionResultPage |
| GET | `/health` | Probe trước khi gửi batch lớn | 200 + HealthStatus |

## 3. Error case Consumer cần xử lý

Tối thiểu 5 case.

| Status | Consumer hiểu là gì? | Consumer sẽ xử lý thế nào? |
|---:|---|---|
| 400 | Request sai schema | Sửa payload, log lỗi |
| 401 | Thiếu token | Refresh/cấu hình token |
| 403 | Không đủ quyền | Báo lỗi quyền truy cập |
| 404 | Không tìm thấy detection | Hiển thị trạng thái không tồn tại |
| 409 | Trùng `requestId` (idempotency) | Nhận kết quả cũ hoặc bỏ qua, không gửi lại |
| 422 | Vi phạm rule nghiệp vụ (ví dụ embedding sai chiều) | Sửa dữ liệu gửi lên |
| 500 | Lỗi phía AI Vision | Retry theo backoff, ghi nhận failure |
| 200 + status LOW_CONFIDENCE | Không đủ chắc chắn để quyết định | Chặn hành động và tạo alert thủ công (KHÔNG coi là lỗi) |

## 4. Giả định bổ sung

- Giả định 1: Core Business gửi `imageRef` hoặc `faceEmbedding`; khi dùng embedding thì `imageRef` phải null và ngược lại.
- Giả định 2: Ngưỡng mặc định `minConfidence = 0.7`; Core có thể gửi ngưỡng riêng theo từng tình huống nghiệp vụ.
- Giả định 3: Mọi request phải mang `requestId` (idempotency) và `traceId` (correlation) để audit và chống xử lý lặp khi retry.

## 5. Câu hỏi cho Provider

1. Khi model không chắc chắn, Provider trả `200 + LOW_CONFIDENCE` hay `422`? Core muốn nhận 200 để tự quyết định xử lý.
2. `personId` trong NoMatchResult là null hay là ứng viên gần nhất? Nếu là ứng viên gần nhất, Core cần biết để log nhưng không được tự động mở cổng.
3. Có giới hạn kích thước payload khi gửi `faceEmbedding` (tối đa bao nhiêu chiều) không?

## 6. Rủi ro tích hợp

| Rủi ro | Tác động | Đề xuất xử lý |
|---|---|---|
| Provider đổi `status` enum | Core parse lỗi | Chốt enum + discriminator trong `openapi.yaml` |
| Retry gây xử lý lặp | Trùng alert/detection | Bắt buộc `requestId` làm idempotency key, `409` khi trùng |
| Timeout downstream | Core bỏ qua người thật | Chốt timeout và policy retry trong negotiation |