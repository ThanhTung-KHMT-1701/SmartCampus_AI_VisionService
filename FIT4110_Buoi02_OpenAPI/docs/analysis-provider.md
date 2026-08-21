# Phân tích yêu cầu — vai Provider

- Cặp đàm phán: Pair 01 (Camera Stream → AI Vision), Pair 02 (Core Business → AI Vision)
- Product: A
- Provider service: AI Vision Service (A4)
- Consumer service: Camera Stream (A2), Core Business (A6)
- Người viết: AI Vision Team
- Ngày: 2026-08-11

---

## 1. Resource chính

| Resource | Mô tả | Thuộc tính bắt buộc | Thuộc tính tùy chọn |
|---|---|---|---|
| Detection | Kết quả phát hiện đối tượng | detection_id, camera_id, detections[], risk_level, model_version, processing_time_ms, timestamp | - |
| FaceMatch | Kết quả so khớp khuôn mặt | match_id, matched, confidence, threshold, status, model_version, processing_time_ms, trace_id, timestamp | message |
| ModelInfo | Thông tin model AI | model_id, model_type, framework, framework_version, classes[], input_size, status | accuracy_map, inference_time_ms_avg, last_updated |

---

## 2. Action/API dự kiến

| Method | Path | Mục đích | Consumer gọi khi nào? |
|---|---|---|---|
| GET | `/health` | Kiểm tra service còn hoạt động | Health check, load balancer |
| POST | `/vision/detect` | Nhận ảnh và phát hiện đối tượng | Camera Stream phát hiện motion, cần AI phân tích |
| GET | `/vision/detections/{detectionId}` | Lấy kết quả detection đã xử lý | Core Business cần audit, Camera Stream cần xác nhận |
| GET | `/vision/results/recent` | Lấy danh sách detection gần đây | Core Business/Analytics cần tổng hợp dữ liệu |
| POST | `/vision/face-match` | So khớp khuôn mặt | Core Business cần xác minh danh tính người |
| GET | `/vision/models/info` | Lấy thông tin model AI đang dùng | Monitoring/Analytics cần biết model version |

---

## 3. Error case

Tối thiểu 5 case.

| Status | Tình huống | Response body dự kiến |
|---:|---|---|
| 400 | Payload sai định dạng JSON hoặc thiếu required field | `Problem` with validation errors |
| 401 | Thiếu hoặc sai Bearer token | `Problem` unauthorized |
| 403 | Token hợp lệ nhưng service không có quyền | `Problem` forbidden |
| 404 | Detection ID không tồn tại hoặc đã hết hạn | `Problem` not found |
| 408 | Request timeout - xử lý mất quá lâu | `Problem` timeout |
| 413 | Payload quá lớn (ảnh > 10MB) | `Problem` payload too large |
| 422 | Payload đúng format nhưng nghiệp vụ không hợp lệ (VD: ảnh format không support) | `Problem` business rule violation |
| 500 | Lỗi không mong muốn phía server (model crash, memory error) | `Problem` internal error |
| 503 | Service tạm thời không khả dụng (model đang load, maintenance) | `Problem` service unavailable |

---

## 4. Giả định bổ sung

Ghi rõ những điểm user story chưa nói nhưng Provider cần giả định.

- **Giả định 1**: Camera Stream gửi ảnh qua URL (`image_url`) thay vì Base64 để giảm payload size. Base64 chỉ dùng khi URL không khả dụng.
- **Giả định 2**: Ảnh gửi lên phải có định dạng JPEG, PNG, hoặc WebP. GIF và các format khác không được hỗ trợ.
- **Giả định 3**: Detection results được lưu trong memory cache tối đa 24 giờ. Sau đó sẽ trả 404 nếu truy vấn.
- **Giả định 4**: Ngưỡng confidence mặc định là 0.5. Consumer có thể override bằng `confidence_threshold` field.
- **Giả định 5**: Timeout cho mỗi request detection là 30 giây. Nếu vượt quá sẽ trả 408.
- **Giả định 6**: Risk level được tính dựa trên detections: LOW (chỉ person), MEDIUM (có vehicle), HIGH (nhiều person), CRITICAL (weapon/anomaly).
- **Giả định 7**: Face match results không được lưu trữ lâu dài, chỉ trả về real-time. Consumer nào cần lưu phải tự lưu.

---

## 5. Câu hỏi cho Consumer

1. **Camera Stream**: Camera có gửi kèm `trace_id` để correlate logs không? Hay chỉ dùng `camera_id` + `timestamp`?
2. **Core Business**: Face match cần lưu trữ results lâu dài không, hay chỉ cần real-time response?
3. **Both**: Ngưỡng confidence 0.5 mặc định có phù hợp không, hay cần điều chỉnh theo use case cụ thể?
4. **Both**: Có cần hỗ trợ async processing (trả 202 + polling) thay vì sync (200) không?

---

## 6. Rủi ro tích hợp

| Rủi ro | Tác động | Đề xuất xử lý |
|---|---|---|
| Tên field không thống nhất (VD: `cameraId` vs `camera_id`) | Consumer parse lỗi | Chốt naming convention snake_case trong `openapi.yaml` |
| Payload lớn (Base64 ảnh 4K) | Timeout, memory error | Thống nhất gửi URL thay vì Base64, giới hạn 10MB |
| Model crash khi inference ảnh corrupt | Service down | Thêm error handling, trả 500 thay vì crash |
| Duplicate detection request | Xử lý lặp, tốn tài nguyên | Consumer gửi idempotency key nếu cần |
| Consumer không xử lý đúng 422 | Bỏ qua cảnh báo nghiệp vụ | Document rõ ràng response codes và xử lý |
