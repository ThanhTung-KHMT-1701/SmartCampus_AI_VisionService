# Ví dụ Boundary: AI Vision

- **Responsibility:** nhận ảnh/frame và trả kết quả phát hiện cùng confidence.
- **Out of scope:** không quyết định có gửi cảnh báo; không gửi Telegram/email.
- **Input:** camera_id, image_url/base64, timestamp.
- **Output:** detection_id, label, confidence, model_version.
- **Consumers:** Camera Stream, Core Business.
