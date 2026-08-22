# Session 0 — Preparation

## Why before how

Service work depends on a consistent toolchain. Verify it now; otherwise a later API or Docker failure may be an environment problem rather than your implementation.

Install Git, Docker Desktop/Engine with Docker Compose, Node.js LTS (20+), Python 3.11+ (or Miniconda), VS Code, and Postman. Then run:

```bash
git --version
docker --version
docker compose version
node --version
python --version || python3 --version
docker run --rm hello-world
```

Create your personal portfolio before this lab. Clone [FIT4110_setup](https://github.com/TrangLe1912/FIT4110_setup) separately, copy it into `01_Setup/` without its `.git` directory, then follow its platform-specific scripts from `01_Setup/`. Retain the generated `evidence/buoi-01/` files there.

If Docker cannot connect, open Docker Desktop and wait for it to become ready. For a port collision, inspect the port first (`lsof -i :8000` on macOS/Linux; `netstat -ano | findstr :8000` on Windows). See [Troubleshooting](../03_Guides/Troubleshooting.md).

---

# Bản dịch tiếng Việt

## Vì sao phải chuẩn bị trước?

Công việc service phụ thuộc vào bộ công cụ nhất quán. Kiểm tra ngay từ đầu để phân biệt lỗi môi trường với lỗi API/Docker sau này.

Cài Git, Docker Desktop/Engine kèm Docker Compose, Node.js LTS (20+), Python 3.11+ hoặc Miniconda, VS Code và Postman. Chạy đúng các lệnh kiểm tra ở phần tiếng Anh; không dịch hay thay đổi lệnh.

Tạo portfolio cá nhân trước Lab này. Clone riêng `FIT4110_setup`, sao chép vào `01_Setup/` mà không mang theo thư mục `.git`, sau đó làm theo script theo hệ điều hành từ `01_Setup/`. Lưu `evidence/buoi-01/` được sinh ra ngay tại thư mục đó. Nếu Docker không kết nối được, mở Docker Desktop và chờ sẵn sàng; nếu trùng port, kiểm tra tiến trình đang giữ port trước khi dừng nó.
