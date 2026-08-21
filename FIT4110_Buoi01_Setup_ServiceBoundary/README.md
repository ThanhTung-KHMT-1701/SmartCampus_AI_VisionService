# FIT4110 – Buổi 1
## Chuẩn bị môi trường và xác định Service Boundary

> Mục tiêu không phải “cài được phần mềm”, mà là tạo ra **minh chứng có thể kiểm tra lại** và xác định rõ service nhóm sẽ xây dựng.

## Sau buổi học, sinh viên làm được gì?

1. Kiểm tra Git, Docker, Docker Compose, Node.js và Python.
2. Chạy được container cơ bản và mini-stack Compose.
3. Đọc log `PASS / WARN / FAIL` và ghi lại lỗi còn tồn tại.
4. Phân biệt actor, provider, consumer, upstream, downstream và service boundary.
5. Hoàn thiện `evidence/buoi-01/service-boundary.md`.
6. Đẩy bài lên repository GitHub cá nhân và nộp link qua Google Sheet.

## Quy trình nhanh

```text
Giải nén ZIP → mở Docker Desktop → pull image lõi → smoke test
→ thu evidence → viết service boundary → verify → commit/push
```

### Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\pull_core.ps1
.\scripts\smoke_test.ps1
.\scripts\collect_evidence.ps1
python .\scripts\verify_submission.py
```

### macOS/Linux

```bash
chmod +x scripts/*.sh
./scripts/pull_core.sh
./scripts/smoke_test.sh
./scripts/collect_evidence.sh
python3 scripts/verify_submission.py
```

## Image được chia hai mức

- **Bắt buộc Buổi 1:** `hello-world`, `python:3.11-slim`, `node:20-alpine`, `nginx:alpine`, `redis:7-alpine`, `registry:2`.
- **Tải trước cho các buổi sau:** PostgreSQL, RabbitMQ, Mosquitto, Traefik, Swagger UI, Prometheus, Grafana và Ultralytics.

Không nên kéo toàn bộ image trong giờ học nếu mạng phòng lab yếu.

## Artefact bắt buộc

```text
evidence/buoi-01/
├── README.md
├── checklist.md
├── known-issues.md
├── tool-versions.txt
├── docker-version.txt
├── compose-version.txt
├── hello-world.txt
├── image-list.txt
├── smoke-test-result.txt
├── git-log.txt
└── service-boundary.md
```


    ## Nộp bằng repository GitHub cá nhân

    Sau khi giải nén và hoàn thành bài:

    ```bash
    git init
    git branch -M main
    git add .
    git commit -m "Complete FIT4110 lab"
    git remote add origin https://github.com/<username>/FIT4110-<MSSV>-<lab01>.git
    git push -u origin main
    ```

    Repository nên để **Public** và đặt tên `FIT4110-<MSSV>-<lab01>` hoặc theo quy ước giảng viên.
    Sinh viên mở link bằng cửa sổ ẩn danh để kiểm tra quyền truy cập, sau đó điền link vào Google Sheet.

    Không commit `.env`, mật khẩu, token thật, `node_modules/`, `.venv/`, model hoặc dataset lớn.


## Điều kiện hoàn thành

- Không còn `[FAIL]` trong `smoke-test-result.txt`, hoặc lỗi được giảng viên chấp nhận và giải thích trong `known-issues.md`.
- `service-boundary.md` có Actor, Responsibility, Out of scope, Input, Output, Provider, Consumer, API/Event dự kiến và sơ đồ.
- Chạy `verify_submission.py` nhận kết quả `PASS`.
