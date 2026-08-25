# FIT4110_lab05_docker_compose_readiness

**Học phần:** FIT4110 – Dịch vụ kết nối và Công nghệ nền tảng  
**Buổi 5:** Điều phối đa dịch vụ với Docker Compose, readiness & AI service  
**Case study:** Smart Campus Operations Platform  
**Repo nền:** `FIT4110_lab04_docker_packaging`

> Lab 04 đã chứng minh rằng một API chạy trên máy cá nhân có thể được đóng gói thành container và kiểm thử lại bằng Postman/Newman.  
> Lab 05 mở rộng tư duy đó: thay vì một container đơn lẻ, chúng ta phải phối hợp **nhiều** dịch vụ thông qua Docker Compose. Đây là bước đệm trực tiếp để tham gia plug‑a‑thon – nơi mọi nhóm gắn kết dịch vụ của mình vào một hệ sinh thái chung.

---

## 1. Ý tưởng nối tiếp từ Lab 04 sang Lab 05

Trong Lab 04, luồng làm việc tập trung vào việc kiểm thử một service được đóng gói trong Docker:

```text
OpenAPI Contract → Service → Dockerfile → Docker image → Docker container → Newman report
```

Lab 05 mở rộng luồng đó thành:

```text
OpenAPI Contract
→ Service thật (API)
→ AI service (ví dụ YOLO v8 hoặc model mock)
→ Database (PostgreSQL hoặc TimescaleDB)
→ Docker Compose định nghĩa toàn bộ stack
→ Nhiều container cùng chạy trên mạng nội bộ `team-internal`
→ Service API gọi được AI và DB qua nội bộ
→ Postman/Newman test lại stack end‑to‑end
→ Evidence (report, log, screenshots)
```

Thông điệp chính của buổi học:

> Một container đơn lẻ chưa đủ – các service thực tế luôn phải tương tác với cơ sở dữ liệu và/hoặc AI/ML.  
> Docker Compose giúp định nghĩa mối quan hệ giữa chúng, nhưng mỗi service vẫn phải tuân thủ các nguyên tắc về readiness, health check và môi trường.

---

## 2. Mục tiêu sau buổi lab

Sau khi hoàn thành Lab 05, mỗi nhóm cần làm được:

- Viết `docker-compose.yml` để định nghĩa ít nhất ba service: API, AI (hoặc worker) và database.
- Dùng network `team-internal` để giao tiếp nội bộ và tham gia mạng chung `class-net` khi cần thiết.
- Chạy API bằng non‑root user trong container và giữ nguyên `HEALTHCHECK` như Lab 04.
- Thêm healthcheck cho DB (`pg_isready`) và AI service để Compose biết khi nào container sẵn sàng.
- Tách cấu hình runtime qua `.env.example` (ví dụ `APP_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `SERVICE_VERSION`, `AUTH_TOKEN`).
- Không commit secret thật vào repo.
- Triển khai `Makefile` hoặc script để nhanh chóng chạy Compose (`make compose-up`, `make compose-down`).
- Viết `RUN_COMPOSE.md` hướng dẫn người khác clone và chạy lại toàn bộ stack.
- Chạy lại Postman/Newman để kiểm thử API trong môi trường Compose (có thể tái sử dụng collection và environment của Lab 04).
- Soạn **checklists/readiness-checklist.md** mô tả checklist readiness 6 điểm (sẵn sàng DB, AI, token, port, network, version) và tick khi hoàn thành.
- Cung cấp bằng chứng (screenshot/ảnh, báo cáo test) trong thư mục `reports/`.

---

## 3. Cấu trúc repo

```text
FIT4110_lab05_docker_compose_readiness/
├── README.md
├── RUN_COMPOSE.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── Makefile
├── requirements.txt
├── src/
│   ├── iot_app/
│   │   ├── __init__.py
│   │   └── main.py
│   └── ai_service/
│       └── main.py
├── contracts/
│   └── iot-ingestion.openapi.yaml
├── postman/
│   └── environments/
│       └── FIT4110_lab05_local.postman_environment.json
├── checklists/
│   └── readiness-checklist.md
└── reports/
```

Thư mục `src/iot_app` chứa API FastAPI giống Lab 04. Thư mục `src/ai_service` chứa service AI mẫu (giả lập), cung cấp một endpoint `/predict` trả về kết quả dummy. Nhóm có thể thay bằng mô hình thực tế (YOLOv8, MediaPipe…).

---

## 4. Chuẩn bị môi trường

Trước khi chạy compose, hãy cài:

- **Git** để clone repo.
- **Docker Desktop** hoặc Docker Engine hỗ trợ Compose v2.
- **Node.js 20.x LTS** và `npm` nếu muốn chạy Newman/Prism/Spectral.
- **Postman Desktop** hoặc Postman Web.

Sau khi clone, cài dependencies phục vụ Prism, Spectral và Newman (tùy chọn):

```bash
npm install
```

Kiểm tra phiên bản:

```bash
docker compose version
docker --version
node --version
npx newman --version
npx prism --version
```

---

## 5. Chạy API local không dùng Docker

Các bước giống Lab 04:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn iot_app.main:app --app-dir src --host 0.0.0.0 --port 8000
```

Kiểm tra health:

```bash
curl http://localhost:8000/health
```

---

## 6. Điều phối đa dịch vụ với Docker Compose

File `docker-compose.yml` định nghĩa 3 service: `api`, `db` và `ai-service`. Các biến môi trường được đặt trong `.env.example` và các volume/network được khai báo rõ ràng.

Chạy compose (build & run):

```bash
docker compose up -d --build
```

Compose sẽ kéo hoặc build image, tạo mạng `team-internal`, gắn volume DB và khởi động lần lượt `db` → `ai-service` → `api`. Bạn có thể theo dõi log:

```bash
docker compose logs -f
```

Kiểm tra readiness của từng service:

- API: `curl http://localhost:8000/health`
- DB: `docker exec -it fit4110-db-lab05 pg_isready -U $POSTGRES_USER`
- AI: `curl http://localhost:9000/health` (service mẫu trả về JSON đơn giản)

Sau khi stack đã sẵn sàng, chạy lại Postman collection giống Lab 04 (sửa `baseUrl` thành `http://localhost:8000`).

Dừng toàn bộ stack:

```bash
docker compose down
```

---

## 7. Readiness checklist

Phần này ghi lại checklist readiness cần kiểm tra trước khi tuyên bố stack sẵn sàng. Xem file [`checklists/readiness-checklist.md`](checklists/readiness-checklist.md) để biết chi tiết và tick vào các mục như:

- DB đã khởi động và sẵn sàng (`pg_isready`).
- AI service đã tải mô hình (nếu có) và có health check trả 200.
- API có thể kết nối DB và AI (ví dụ tạo một reading thành công).
- Các biến môi trường (.env) được đặt đúng, không dùng secret thật.
- `team-internal` network hoạt động; service có thể gọi nội bộ qua tên container.
- Version/tag của từng image được cập nhật đúng quy ước (vd: `v0.1.0-team-iot`).

---

## 8. Các lệnh nhanh bằng Makefile

Makefile cung cấp các lệnh tiện lợi:

```bash
make compose-up      # build và chạy compose stack
make compose-down    # stop và remove stack
make logs            # theo dõi log của các service
make test-compose    # chạy newman test trên compose (tùy chọn)
```

Bạn có thể mở Makefile để chỉnh sửa thêm các mục.

---

## 9. Bài làm của từng nhóm

Mỗi nhóm dùng repo này làm mẫu và thay thế service trong `src/` bằng service của mình.

| Nhóm         | Cần thay đổi |
|--------------|-------------|
| `team-iot`   | Có thể sử dụng API IoT mẫu, thêm DB TimescaleDB nếu muốn. |
| `team-camera`| Thay `src/ai_service` bằng service Camera Stream & AI inference, cập nhật port và health. |
| `team-gate`  | Kết nối API với Access Gate service, lưu ý biến môi trường DB cho cổng, bỏ AI nếu không cần. |
| `team-vision`| Thay `ai_service` bằng mô hình YOLOv8/MediaPipe; đảm bảo container đủ dependency CUDA khi cần. |
| `team-analytics`| Thay DB bằng TimescaleDB, service analytics sẽ đọc dữ liệu và trả về thống kê. |
| `team-core`  | Thay API thành policy engine; có thể bỏ AI/DB nếu không dùng. |
| `team-notify`| Thay API thành Notification service, thêm RabbitMQ hoặc gửi email/SMS; không commit token thật. |

---

## 10. Điều kiện hoàn thành Lab 05

Một nhóm được xem là hoàn thành Lab 05 khi:

- `docker-compose.yml` khởi tạo ít nhất 3 container và khai báo đúng network/volume.
- Mỗi service có `HEALTHCHECK` và container được chạy bằng user non‑root (nếu tự build).
- `.dockerignore`, `.env.example`, `RUN_COMPOSE.md` đầy đủ, không rò rỉ secret.
- `db` và `ai-service` sẵn sàng trước khi API start (Compose `depends_on` và health check). 
- Postman/Newman test pass trên API khi chạy trong stack Compose.
- Có report trong `reports/` (XML/HTML) và evidence log/ảnh chụp health.
- Version/tag của image tuân theo quy ước `v0.1.0-<team>`, push lên registry (ghcr.io hoặc Docker Hub).

---

## 11. Artefact cần nộp

```text
docker-compose.yml
.dockerignore
.env.example
RUN_COMPOSE.md
contracts/<team>.openapi.yaml
postman/environments/<team>_local.postman_environment.json
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
ảnh chụp /health hoặc log container
tag image đã push lên registry
checklists/readiness-checklist.md (đã tick các mục)
```

---

## 12. Rubric gợi ý

| Tiêu chí                                              | Điểm |
|-------------------------------------------------------|-----:|
| `docker-compose.yml` đúng, build & run được           | 2.0 |
| Các container sẵn sàng, `/health` và DB/AI pass        | 2.0 |
| Non‑root, `.dockerignore`, `.env.example` tốt         | 1.5 |
| Newman/Postman test pass trên stack Compose           | 2.0 |
| `RUN_COMPOSE.md` rõ ràng, người khác chạy lại được    | 1.5 |
| Evidence đầy đủ: log/report/image tag & checklist     | 1.0 |
| **Tổng**                                             | **10.0** |

---

## 13. Tinh thần của buổi học

Sau Buổi 4, nhóm đã chứng minh:

```text
API có thể chạy trong container và được kiểm thử tự động.
```

Sau Buổi 5, nhóm cần chứng minh thêm:

```text
Hệ thống nhiều service có thể phối hợp trơn tru thông qua Docker Compose, với readiness rõ ràng và kiểm thử end‑to‑end.
```

Điều này là tiền đề để chuẩn bị cho plug‑a‑thon, nơi các nhóm sẽ “cắm vào” hệ sinh thái chung của lớp và vận hành nhiều service cùng lúc.
