# FIT4110 — Buổi 5: AI Vision trong Docker + MySQL Database

## Mục tiêu

| Service | Trạng thái | Vị trí |
|---|---|---|
| AI Vision Service | Đóng gói Docker (image `fit4110/ai-vision:lab05`) | Container |
| MySQL Database | Đóng gói Docker (image `mysql:8.0`) | Container |
| Camera Stream Mock | **KHÔNG** đóng gói | Host (LAN IP thật) |
| Core Business Mock | **KHÔNG** đóng gói | Host (LAN IP thật) |

## Tính năng mới

- **MySQL Database**: Lưu trữ kết quả detection và face-match vào database thay vì in-memory
- **Persistence**: Dữ liệu được lưu vĩnh viễn, không mất khi restart service
- **Connection Pooling**: Sử dụng MySQL connection pool để tối ưu hiệu suất

## Cấu hình Database

### Biến môi trường

```env
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=ai_vision_db
```

### Docker Compose (tự động)

Khi chạy với `docker compose`, MySQL được cấu hình tự động:
- Host: `mysql` (internal Docker network)
- Database: `ai_vision_db`
- Init script: `database/AI_Vision_Service.sql` chạy tự động khi tạo container

## Khởi tạo Database (Local - không Docker)

```powershell
# 1. Đăng nhập MySQL
mysql -u root -p

# 2. Chạy script tạo database và dữ liệu mẫu
source "e:\dnu.khmt.1701.1771040029@gmail.com\GithubClassroom\SmartCampus_AI_VisionService\FIT4110_Buoi05\database\AI_Vision_Service.sql"

# 3. Cập nhật .env với password thật
# MYSQL_PASSWORD=your_actual_password
```

## Build & Run

### Cách 1: Docker Compose (Khuyến nghị)

```powershell
cd "e:\dnu.khmt.1701.1771040029@gmail.com\GithubClassroom\SmartCampus_AI_VisionService\FIT4110_Buoi05"

# Copy và chỉnh sửa .env
Copy-Item -Force .env.example .env
# Chỉnh sửa MYSQL_PASSWORD trong .env

# Build và chạy
docker compose build
docker compose up -d

# Kiểm tra trạng thái
docker compose ps
```

### Cách 2: Chạy Local (Python trực tiếp)

```powershell
cd "e:\dnu.khmt.1701.1771040029@gmail.com\GithubClassroom\SmartCampus_AI_VisionService\FIT4110_Buoi05"

# Tạo virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy service
python -m uvicorn ai_vision_service.main:app --host 0.0.0.0 --port 8000 --reload
```

## Verify

```powershell
# Health check
curl.exe http://localhost:8000/health | python -m json.tool

# Kiểm tra database
mysql -u root -p -e "USE ai_vision_db; SELECT COUNT(*) as total FROM detections;"
```

## Test end-to-end

Camera Mock chạy ngoài host (IP `192.168.137.115:8001` theo `.env.example`) → POST frame:

```powershell
curl.exe -X POST http://192.168.137.115:8001/frames `
  -H "Authorization: Bearer lab-token-camera" `
  -H "Content-Type: application/json" `
  -d '{"camera_id":"cam-lab05-01","frame_url":"http://storage.local/f.jpg","motion_detected":true,"timestamp":"2026-08-25T01:00:00Z"}'
```

AI Vision (trong Docker) — gọi detect:

```powershell
curl.exe -X POST http://localhost:8000/vision/detect `
  -H "Authorization: Bearer local-dev-token-vision" `
  -H "Content-Type: application/json" `
  -d '{"camera_id":"cam-lab05-01","image_url":"http://192.168.137.115:8001/cameras/cam-lab05-01/frames/latest","timestamp":"2026-08-25T01:00:00Z"}'
```

## Kiểm thử API thật (Postman + Newman + Scripts)

Sau khi Docker container đang chạy, có 3 cách kiểm thử service thật:

### Cách 1 — Smoke test nhanh (không cần Postman)

```powershell
.\scripts\contract-smoke.ps1
```

Script chạy 15 request bằng `Invoke-WebRequest`, in `[PASS]` / `[FAIL]` cho từng case.

### Cách 2 — 18 test cases với Postman CLI + evidence

```powershell
.\scripts\run-18-test-cases.ps1
```

Sinh evidence tại `reports/evidence/TC01.stdout.txt` ... `TC18.stdout.txt` và summary `results.json`.

### Cách 3 — Newman HTML / JUnit report

```powershell
npm install -g newman
.\scripts\collect-evidence.ps1
```

Sinh `reports/vision-newman-report-docker-latest.html` (mở bằng browser) và `.xml`.

### Cách 4 — Postman UI

Import 2 file trong `postman/`:
- Collection: `postman/collections/FIT4110_lab05_ai_vision_real.postman_collection.json`
- Environment: `postman/environments/FIT4110_lab05_docker_local.postman_environment.json`

## Cấu trúc thư mục

```
FIT4110_Buoi05/
├── src/ai_vision_service/        # Service code đóng gói vào Docker
│   ├── main.py                   # FastAPI app
│   ├── schemas.py                # Pydantic models
│   └── store.py                  # MySQL store (thay thế in-memory)
├── database/
│   └── AI_Vision_Service.sql     # Schema + dữ liệu mẫu
├── postman/
│   ├── collections/              # FIT4110_lab05_ai_vision_real.postman_collection.json
│   └── environments/             # docker-local + lan-remote
├── scripts/                      # contract-smoke / run-18-test-cases / collect-evidence
├── mock-data/                    # Sample request bodies cho Postman / scripts
├── reports/                      # Newman HTML/XML + evidence per test case
│   ├── README.md
│   ├── vision-newman-report-docker-latest.html
│   └── evidence/                 # TC01.stdout.txt ... TC18.stdout.txt
├── docs/
│   ├── BAO_CAO_TONG_QUAN.md
│   ├── BAO_CAO_API.md
│   └── HUONG_DAN_CHAY_TESTS.md
├── consumer-provider-handshake.md # Biên bản thỏa thuận hợp đồng
├── test-case-matrix.csv          # Ma trận 18 test cases
├── Dockerfile
├── docker-compose.yml            # Bao gồm MySQL service
├── requirements.txt             # Bao gồm mysql-connector-python
├── .env.example                  # Bao gồm MySQL config
├── .env                          # Config local (không commit)
└── README.md
```

## Database Schema

### Bảng `detections`

| Column | Type | Description |
|--------|------|-------------|
| detection_id | CHAR(36) | UUID - Primary Key |
| camera_id | VARCHAR(80) | ID camera nguồn |
| detections | JSON | Danh sách objects phát hiện |
| risk_level | ENUM | LOW, MEDIUM, HIGH, CRITICAL |
| model_version | VARCHAR(50) | Phiên bản AI model |
| processing_time_ms | INT | Thời gian xử lý |
| timestamp | DATETIME | Thời điểm xử lý |
| created_at | DATETIME | Thời điểm lưu vào DB |

### Bảng `face_matches`

| Column | Type | Description |
|--------|------|-------------|
| match_id | CHAR(36) | UUID - Primary Key |
| matched | BOOLEAN | Kết quả khớp |
| confidence | DECIMAL | Độ tin cậy (0.0000-1.0000) |
| threshold | DECIMAL | Ngưỡng so sánh |
| status | ENUM | MATCHED, NOT_MATCHED, LOW_CONFIDENCE, ERROR |
| message | VARCHAR(500) | Mô tả kết quả |
| model_version | VARCHAR(50) | Phiên bản model |
| processing_time_ms | INT | Thời gian xử lý |
| trace_id | VARCHAR(100) | Trace ID cho audit |
| timestamp | DATETIME | Thời điểm xử lý |
| created_at | DATETIME | Thời điểm lưu vào DB |

### Bảng `model_info`

| Column | Type | Description |
|--------|------|-------------|
| id | INT | Auto-increment Primary Key |
| model_id | VARCHAR(50) | ID model (unique) |
| model_type | ENUM | Loại model |
| framework | VARCHAR(50) | Framework AI |
| framework_version | VARCHAR(20) | Phiên bản framework |
| classes | JSON | Danh sách classes |
| confidence_threshold_default | DECIMAL | Ngưỡng mặc định |
| input_size | INT | Kích thước input |
| accuracy_map | DECIMAL | Độ chính xác mAP |
| inference_time_ms_avg | INT | Thời gian inference TB |
| status | ENUM | ACTIVE, LOADING, ERROR, DEPRECATED |

## Dọn dẹp

```powershell
# Dừng và xóa containers
docker compose down

# Xóa cả database volume (mất dữ liệu!)
docker compose down -v

# Xóa images
docker compose down --rmi all
```

---

## Troubleshooting

### Lỗi kết nối MySQL

```powershell
# Kiểm tra MySQL container đang chạy
docker compose ps

# Xem logs
docker compose logs mysql

# Kiểm tra kết nối từ app
docker compose exec ai-vision python -c "import mysql.connector; print('OK')"
```

### Khôi phục dữ liệu mẫu

```powershell
docker compose exec mysql mysql -u root -p -e "USE ai_vision_db; SOURCE /docker-entrypoint-initdb.d/AI_Vision_Service.sql;"
```
