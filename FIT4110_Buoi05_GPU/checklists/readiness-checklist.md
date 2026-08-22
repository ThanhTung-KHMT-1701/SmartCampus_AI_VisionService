# Readiness Checklist – Lab 05

Đây là danh sách kiểm tra (checklist) để đảm bảo stack Docker Compose của bạn đã sẵn sàng trước khi gửi bài. Hãy tick vào mỗi mục sau khi hoàn thành.

---

## Cách kiểm tra nhanh

Chạy lần lượt từng lệnh bên dưới trong terminal (PowerShell/Git Bash):

```bash
# 1. Kiểm tra container đang chạy
docker compose ps

# 2. API health
curl http://localhost:8000/health

# 3. AI service health
curl http://localhost:9000/health
```

---

## Checklist

- [ ] **API ready:** container `fit4110-ai-vision-lab05` trả `200` cho `/health`.

- [ ] **AI inference service ready:** container `fit4110-ai-lab05` trả về `200` cho endpoint `/health`.

- [ ] **Environment variables:** `.env` đã được thiết lập đúng (APP_PORT, AI_VISION_AUTH_TOKEN,…). Không sử dụng secret thật; lưu secret vào `.env` cục bộ, commit `.env.example`.

- [ ] **Network & Ports:** mạng `team-internal` hoạt động; ports 8000 (API) và 9000 (AI) được map đúng.

- [ ] **Thứ tự khởi động:** `ai-service` khởi động trước `api` (dùng `depends_on` + healthcheck).

- [ ] **Image tags:** đã build image với tag đúng quy ước. Nếu cần push lên registry, chạy `docker tag` và `docker push`.

---

## Ghi chú thêm

Ghi lại bất kỳ vấn đề nào gặp phải hoặc điều chỉnh đã thực hiện:

```
- …
```
