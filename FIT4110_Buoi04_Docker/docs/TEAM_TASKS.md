# TEAM_TASKS.md – Việc cần làm theo nhóm

Mỗi nhóm bắt đầu từ repo mẫu này và thay phần IoT bằng service của mình.

---

## Việc chung cho mọi nhóm

- [ ] Copy contract từ Lab 03 vào thư mục `contracts/`.
- [ ] Đảm bảo service có `GET /health`.
- [ ] Viết hoặc cập nhật `Dockerfile`.
- [ ] Viết `.dockerignore`.
- [ ] Viết `.env.example`.
- [ ] Viết `RUN_LOCAL.md`.
- [ ] Build image.
- [ ] Run container.
- [ ] Chạy Postman Collection từ Lab 03 trên container.
- [ ] Xuất Newman report.
- [ ] Chụp bằng chứng `/health` hoặc log container.
- [ ] Ghi tag image đã push.

---

## Gợi ý theo service

| Service | Điểm cần chú ý |
|---|---|
| IoT Ingestion | API nhận telemetry, auth token, `/health`, test boundary nhiệt độ |
| Camera Stream | Dùng `opencv-python-headless`, chuẩn bị 1 ảnh mẫu, chưa cần RTSP thật |
| Access Gate | Nếu chưa có DB trong Lab 04, dùng in-memory hoặc DB ngoài; Compose để Buổi 5 |
| AI Vision | Có thể dùng mock model hoặc YOLOv8n nhỏ; kiểm soát dung lượng image |
| Analytics | Nhận event JSON giả; TimescaleDB để Buổi 5 |
| Core Business | Policy evaluation chạy bằng config/env |
| Notification | Channel mock là đủ; không commit Telegram/email token thật |
