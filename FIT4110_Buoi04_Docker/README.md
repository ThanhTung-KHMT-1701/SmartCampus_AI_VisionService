# FIT4110_lab04_ai_vision_docker

**Học phần:** FIT4110 – Dịch vụ kết nối và Công nghệ nền tảng  
**Buổi 4:** Đóng gói service với Docker & tư duy công nghệ nền tảng  
**Nhóm:** team-vision (Smart Campus Operations Platform)  
**Service chính:** AI Vision Service (theo `contracts/ai-vision.openapi.yaml` của Buổi 2)  
**Repo nền:** `FIT4110_Buoi03_Postman_Mock_Testing`

> Buổi 3 đã có OpenAPI contract, Postman Collection, Mock Server, Newman report và service Python thật (AI Vision + 2 side mock).  
> Buổi 4 đóng gói lại các service đó thành Docker image, chạy được bằng `docker compose`, vẫn pass Newman trên container.

---

## 1. Cấu trúc repo

```text
FIT4110_Buoi04_Docker/
├── README.md
├── RUN_LOCAL.md
├── Dockerfile                       # AI Vision Service (8000)
├── Dockerfile.core-mock             # Core Business side mock (4012)
├── Dockerfile.camera-mock           # Camera Stream side mock (4014)
├── docker-compose.yml               # cả 3 service trên network smartcampus-lab-net
├── .dockerignore
├── .gitignore
├── .env.example
├── Makefile
├── package.json
├── requirements.txt                 # FastAPI + uvicorn + pydantic
├── src/
│   ├── ai_vision_service/           # provider thật (chuẩn OpenAPI Buổi 2)
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── store.py
│   └── side_mocks/                  # mock phục vụ consumer-side smoke test
│       ├── core_business.py         # 4012
│       └── camera_stream.py         # 4014
├── contracts/
│   └── ai-vision.openapi.yaml       # hợp đồng Buổi 2 (giữ nguyên)
├── postman/
│   ├── collections/
│   │   └── FIT4110_lab04_ai_vision.postman_collection.json
│   └── environments/
│       ├── FIT4110_lab04_ai_vision_local.postman_environment.json
│       └── FIT4110_lab04_ai_vision_mock.postman_environment.json
├── mock-data/
├── docs/
│   ├── DOCKER_LAB_GUIDE.md
│   ├── TEAM_TASKS.md
│   ├── TROUBLESHOOTING.md
│   └── docker-evidence.md
├── checklists/
│   ├── docker_readiness_checklist.md
│   └── submission_checklist.md
├── reports/
└── .github/workflows/               # (tuỳ chọn) CI build + Newman
```

---

## 2. Thành phần chính

| Service | Port host | Port container | Image | Auth token (mặc định) |
|---|---:|---:|---|---|
| AI Vision Service (`ai-vision`) | 8000 | 8000 | `fit4110/ai-vision:lab04` | `local-dev-token-vision` |
| Core Business mock (`core-business-mock`) | 4012 | 4012 | `fit4110/core-business-mock:lab04` | `lab-token-core` |
| Camera Stream mock (`camera-stream-mock`) | 4014 | 4014 | `fit4110/camera-stream-mock:lab04` | `lab-token-camera` |

Số port **khớp với `scripts/run-service.js`** của Buổi 3 và với `servers[].url` của `ai-vision.openapi.yaml` (Buổi 2 quy ước `http://ai-vision:8000` trong Docker network).

Cả 3 container đều:
- Multi-stage build (`builder` → `runtime`), non-root user `appuser:appgroup`.
- Có `HEALTHCHECK` gọi `GET /health`.
- Mount `src/` từ repo vào `/app/src`, dùng `PYTHONPATH=/app/src` để chạy `uvicorn`.
- Chia sẻ một bridge network `smartcampus-lab-net` để service name resolve nội bộ (`http://ai-vision:8000`, `http://core-business-mock:4012`, `http://camera-stream-mock:4014`).

---

## 3. Chạy nhanh

```bash
# 1. Cài dependencies cho Newman + Spectral
npm install

# 2. Build & chạy 3 container
docker compose up -d --build

# 3. Smoke test 3 service
curl http://localhost:8000/health
curl http://localhost:4012/health
curl http://localhost:4014/health

# 4. Chạy Newman collection trên AI Vision container
npm run test:vision:local

# 5. Xem report
# reports/newman-vision-local.html
# reports/newman-vision-local.xml

# 6. Dừng stack
docker compose down
```

Chi tiết hơn xem [RUN_LOCAL.md](RUN_LOCAL.md).

---

## 4. Điều kiện hoàn thành Lab 04

- [x] `Dockerfile` build được cho cả 3 service.
- [x] Image chạy được container, có `/health` 200.
- [x] Non-root user, `.dockerignore`, `.env.example` đầy đủ.
- [x] Newman/Postman test pass trên AI Vision container.
- [x] `RUN_LOCAL.md` rõ ràng, người khác chạy lại được.
- [x] Evidence: report XML/HTML, log docker, tag image.

Đối chiếu chi tiết trong `checklists/docker_readiness_checklist.md` và `checklists/submission_checklist.md`.
