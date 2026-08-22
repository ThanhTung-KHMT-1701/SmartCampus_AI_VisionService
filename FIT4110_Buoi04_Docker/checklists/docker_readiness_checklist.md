# Docker Readiness Checklist — Lab 04 (team-vision)

## Dockerfile

- [x] Có base image hợp lý (`python:3.11-slim`).
- [x] Có `WORKDIR` (`/app`).
- [x] Copy dependency trước source để tận dụng cache (`requirements.txt` trước `src/`).
- [x] Có `EXPOSE` (8000 / 4012 / 4014).
- [x] Có `CMD` (`uvicorn` qua `sh -c` để đọc ENV).
- [x] Có `HEALTHCHECK` (gọi `GET /health` qua urllib).
- [x] Có user non-root (`appuser:appgroup`).
- [x] Không chứa secret thật (chỉ giá trị dev mặc định, override qua `.env.example`).
- [x] Multi-stage build (`builder` → `runtime`) để giữ image nhỏ.

## Runtime

- [x] Container chạy được (`docker compose up -d --build` thành công).
- [x] Port map đúng (8000/4012/4014 ↔ container).
- [x] `/health` 3 service đều trả `200`.
- [x] Log khởi động rõ ràng (uvicorn log level warning mặc định).
- [x] Cấu hình qua ENV (`AI_VISION_AUTH_TOKEN`, `CORE_AUTH_TOKEN`, `CAMERA_AUTH_TOKEN`, `APP_HOST`, `APP_PORT`).

## Testing

- [x] Chạy lại Postman Collection Vision từ Buổi 3.
- [x] Newman report sinh ra trong `reports/`.
- [x] Functional test pass (folder `01_Functional`).
- [x] Auth test pass trên local/container (folder `02_Auth` — token hợp lệ / thiếu / sai).
- [x] Negative test pass trên local/container (folder `03_Negative`).
- [x] Boundary test pass (folder `04_Boundary_Reliability` — threshold 0.0, limit 100, image_url/base64).
- [x] Consumer-side smoke test gọi được Core Business mock và Camera Stream mock (folder `05_Consumer_side_Smoke`).
- [x] Local-only non-functional test pass (folder `06_Local_only_NonFunctional`).

## Evidence

- [x] Log `docker compose build` (xem `docs/docker-evidence.md` section 1).
- [x] Log `docker compose ps` (section 2).
- [x] 3 response `curl /health` (section 3).
- [x] Newman HTML/XML report (`reports/newman-vision-local.{html,xml}`).
- [x] Tag image đúng quy ước `fit4110/<service>:lab04` (section 7).
- [x] Integration end-to-end Vision → Core Business mock (section 5).
