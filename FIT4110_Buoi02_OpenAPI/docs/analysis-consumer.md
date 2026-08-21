# Phân tích yêu cầu — vai Consumer

- Cặp đàm phán: Pair 01 (Camera Stream → AI Vision), Pair 02 (Core Business → AI Vision)
- Product: A
- Consumer service: Camera Stream (A2), Core Business (A6)
- Provider service: AI Vision Service (A4)
- Người viết: AI Vision Team
- Ngày: 2026-08-11

---

## 1. Resource Consumer cần nhận/gửi

| Resource | Consumer dùng để làm gì? | Field bắt buộc với Consumer | Field có thể tùy chọn |
|---|---|---|---|
| DetectionResult | Hiển thị kết quả phát hiện cho security/gate | detection_id, detections[], risk_level | processing_time_ms, model_version |
| FaceMatchResult | Xác minh danh tính sinh viên/nhân viên | match_id, matched, confidence, status | message, trace_id |
| ModelInfo | Monitoring/logging model version | model_id, model_type, status | accuracy_map, classes[] |

---

## 2. API Consumer cần gọi

| Method | Path | Lúc nào gọi? | Kỳ vọng response |
|---|---|---|---|
| POST | `/vision/detect` | Khi camera phát hiện motion hoặc frame interval | 200 với detection_id và detections[] |
| GET | `/vision/detections/{detectionId}` | Khi cần truy vấn lại kết quả cũ hoặc xác nhận | 200 với chi tiết detection, 404 nếu hết hạn |
| GET | `/vision/results/recent` | Khi Analytics cần tổng hợp dữ liệu | 200 với danh sách detections + pagination cursor |
| POST | `/vision/face-match` | Khi Core Business cần xác minh khuôn mặt | 200 với matched true/false và confidence |
| GET | `/vision/models/info` | Khi monitoring cần biết model version | 200 với thông tin model chi tiết |
| GET | `/health` | Health check, load balancer probe | 200 với status ok |

---

## 3. Error case Consumer cần xử lý

Tối thiểu 5 case.

| Status | Consumer hiểu là gì? | Consumer sẽ xử lý thế nào? |
|---:|---|---|
| 400 | Request sai schema hoặc thiếu required field | Log lỗi, sửa payload, retry |
| 401 | Token không hợp lệ hoặc hết hạn | Refresh token từ auth service, retry |
| 403 | Không có quyền gọi API này | Alert admin, không retry |
| 404 | Detection/Resource không tồn tại | Log warning, không retry |
| 408 | AI Vision xử lý quá chậm | Retry với exponential backoff, có thể giảm ảnh |
| 413 | Ảnh gửi lên quá lớn | Resize ảnh trước khi gửi lại |
| 422 | Nghiệp vụ không hợp lệ (format ảnh không support) | Log chi tiết lỗi, thông báo cho ops |
| 500 | AI Vision lỗi nội bộ | Retry với exponential backoff, alert nếu fail nhiều lần |
| 503 | AI Vision đang bảo trì hoặc overload | Chờ và retry với delay, có thể queue request |

---

## 4. Giả định bổ sung

- **Giả định 1**: Camera Stream sẽ gửi `image_url` thay vì `image_base64` để giảm payload và tăng tốc độ xử lý.
- **Giả định 2**: Detection results có thể truy vấn lại trong vòng 24 giờ sau khi tạo.
- **Giả định 3**: Consumer sẽ tự xử lý risk_level để quyết định có tạo alert hay không (AI Vision không tự tạo alert).
- **Giả định 4**: Face match là real-time operation, không lưu trữ lâu dài trên AI Vision.
- **Giả định 5**: Consumer cần include `trace_id` trong request để correlate logs giữa các services.

---

## 5. Câu hỏi cho Provider

1. **AI Vision**: Detection results có được lưu trong database không, hay chỉ in-memory cache? Duration là bao lâu?
2. **AI Vision**: Có hỗ trợ gửi ảnh qua multipart/form-data thay vì JSON body không? (Có thể hữu ích cho ảnh lớn)
3. **AI Vision**: Risk level được tính như thế nào? Có thể customize được không?
4. **AI Vision**: Face match có lưu trữ results không, hay chỉ return real-time?
5. **AI Vision**: Model có restart/reload thường xuyên không? Có thể gây 503?

---

## 6. Rủi ro tích hợp

| Rủi ro | Tác động | Đề xuất xử lý |
|---|---|---|
| Provider đổi kiểu dữ liệu | Consumer parse lỗi | Chốt type/format/pattern trong openapi.yaml, version API rõ ràng |
| Provider thiếu mã lỗi chi tiết | Consumer không biết xử lý thế nào | Yêu cầu Problem Details format với errors array |
| Provider trả 200 nhưng detections = [] | Consumer hiểu nhầm thành lỗi | Document rõ ràng: empty array là normal result |
| Provider timeout | Consumer chờ vô hạn | Set client-side timeout 30s, retry với backoff |
| Ảnh gửi qua URL không accessible | AI Vision không fetch được ảnh | Dùng URL public hoặc pre-upload ảnh lên accessible storage |
| Model version mismatch | Consumer kỳ vọng field không tồn tại | Consumer check model_version trong response |
