# Submission Checklist – Lab 04 (team-vision)

Nộp các minh chứng sau:

- [x] `Dockerfile` (AI Vision)
- [x] `Dockerfile.core-mock` (Core Business side mock)
- [x] `Dockerfile.camera-mock` (Camera Stream side mock)
- [x] `docker-compose.yml` (chạy cả 3 service trên network `smartcampus-lab-net`)
- [x] `.dockerignore`
- [x] `.env.example`
- [x] `RUN_LOCAL.md`
- [x] Contract OpenAPI đã dùng — `contracts/ai-vision.openapi.yaml` (giữ nguyên từ Buổi 2)
- [x] Postman Collection đã chạy trên container — `postman/collections/FIT4110_lab04_ai_vision.postman_collection.json`
- [x] Postman Environment local/docker — `postman/environments/FIT4110_lab04_ai_vision_local.postman_environment.json`
- [x] Postman Environment mock — `postman/environments/FIT4110_lab04_ai_vision_mock.postman_environment.json`
- [x] Newman report XML — `reports/newman-vision-local.xml`
- [x] Newman report HTML — `reports/newman-vision-local.html`
- [x] Log docker build / docker compose up — `docs/docker-evidence.md` section 1, 2
- [x] Log curl `/health` cho 3 service — `docs/docker-evidence.md` section 3
- [x] Log integration end-to-end Vision → Core Business mock — `docs/docker-evidence.md` section 5
- [x] Tag image đã build — `fit4110/ai-vision:lab04`, `fit4110/core-business-mock:lab04`, `fit4110/camera-stream-mock:lab04`
