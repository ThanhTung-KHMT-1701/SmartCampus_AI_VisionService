# TROUBLESHOOTING.md – Lỗi thường gặp Lab 04

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `Cannot connect to Docker daemon` | Docker Desktop chưa chạy | Mở Docker Desktop, chờ Docker ready |
| `port is already allocated` | Port 8000 đang bị service khác dùng | Dừng service cũ hoặc đổi `-p 8001:8000` |
| `ModuleNotFoundError` | Thiếu dependency hoặc sai `--app-dir` | Kiểm tra `requirements.txt` và lệnh CMD |
| `/health` không phản hồi | App chưa start hoặc sai port | Xem `docker logs <container>` |
| Newman `ECONNREFUSED` | Container chưa chạy hoặc baseUrl sai | Kiểm tra environment Postman |
| Test auth fail | Sai `AUTH_TOKEN` giữa `.env.example` và Postman env | Đồng bộ token |
| Image quá nặng | Copy thừa `.git`, `.venv`, dataset | Sửa `.dockerignore` |
| Container chạy bằng root | Dockerfile chưa tạo user | Thêm `USER appuser` |
| CI fail ở bước Newman | Service chưa ready | Dùng `wait-on` hoặc script wait-for-health |
