# HƯỚNG DẪN CHẠY TEST
## FIT4110 Buổi 5 — AI Vision Docker Service

---

## 1. Yêu cầu môi trường

- **Docker Desktop** (Windows) đang chạy.
- **PowerShell 7+** (đã cài `Invoke-WebRequest` hỗ trợ `-SkipHttpErrorCheck`).
- **Camera Stream mock** chạy ở `http://192.168.137.115:8001` (nếu muốn chạy consumer-side smoke).
- **Postman CLI** (tùy chọn, cho `run-18-test-cases.ps1`).
- **Newman** (tùy chọn, cho `collect-evidence.ps1`).

---

## 2. Chuẩn bị

### 2.1. Khởi động Docker container

```powershell
cd "e:\dnu.khmt.1701.1771040029@gmail.com\GithubClassroom\SmartCampus_AI_VisionService\FIT4110_Buoi05"

# Tạo .env từ .env.example (nếu chưa có)
if (-not (Test-Path .env)) { Copy-Item -Force .env.example .env }

# Build và chạy container
docker compose build
docker compose up -d

# Verify
docker compose ps
```

Container phải listen ở `http://localhost:8000`.

### 2.2. Verify service còn sống

```powershell
curl.exe http://localhost:8000/health
```

Phải trả về JSON với `status: "ok"`.

### 2.3. Cấu hình Postman

1. Import collection: `postman/collections/FIT4110_lab05_ai_vision_real.postman_collection.json`
2. Import environment: `postman/environments/FIT4110_lab05_docker_local.postman_environment.json`
3. (Tùy chọn) Import environment LAN remote nếu test từ máy khác.
4. Chọn environment `FIT4110 Lab05 Docker Real Service` ở dropdown trên cùng bên phải.

---

## 3. Cách chạy tests

### 3.1. Smoke test nhanh (15 requests, không cần Postman CLI)

Script dùng `Invoke-WebRequest` — chạy được trên PowerShell 5+.

```powershell
.\scripts\contract-smoke.ps1
```

Output: danh sách 15 requests với `[PASS]` / `[FAIL]` marker.

---

### 3.2. 18 test cases với Postman CLI (có evidence per case)

```powershell
# Cài Postman CLI nếu chưa có
# Download: https://www.postman.com/downloads/

# Login (cần API key)
postman login --with-api-key <YOUR_POSTMAN_API_KEY>

# Chạy 18 test cases
.\scripts\run-18-test-cases.ps1
```

Output:
- `reports/evidence/TC01.stdout.txt` ... `TC18.stdout.txt` — raw stdout của postman CLI
- `reports/evidence/TC*.body.json` — request body
- `reports/evidence/results.json` — tổng hợp kết quả

---

### 3.3. Newman HTML/JUnit report (cần newman)

```powershell
# Cài newman
npm install -g newman

# Chạy full collection + sinh HTML report
.\scripts\collect-evidence.ps1
```

Output:
- `reports/vision-newman-report-docker-<timestamp>.html` — mở được trên browser
- `reports/vision-newman-report-docker-<timestamp>.xml` — JUnit XML cho CI
- `reports/vision-newman-report-docker-latest.html` — alias bản mới nhất

---

### 3.4. Chạy trong Postman UI

1. Mở Postman → import collection.
2. Chọn environment `FIT4110 Lab05 Docker Real Service`.
3. Mở rộng folder `00_Health` → `01_Functional` → ... → click **Send** trên từng request.
4. Mỗi request có test scripts tự động kiểm tra response.
5. Để chạy cả collection: click chuột phải vào root collection → **Run folder**.

---

## 4. Test case coverage

| Folder | Số test | Mục đích |
|---|---|---|
| 00_Health | 1 | Service alive |
| 01_Functional | 6 | Happy paths |
| 02_Auth | 4 | Bearer token thật |
| 03_Negative | 7 | Validation error |
| 04_Boundary_Reliability | 4 | Edge values |
| 05_Consumer_side_Smoke | 2 | Camera Stream LAN smoke |
| 06_Local_only_NonFunctional | 3 | Performance SLA |
| **Tổng** | **27 requests** | |

Test cases riêng trong `run-18-test-cases.ps1` (Postman CLI):
- TC01-TC18 — đầy đủ chức năng, auth, validation, consumer-side smoke.

Xem chi tiết: `test-case-matrix.csv`.

---

## 5. Xem evidence sau khi chạy

```powershell
# Mở Newman HTML report
Start-Process reports\vision-newman-report-docker-latest.html

# Xem summary kết quả 18 test cases
Get-Content reports\evidence\results.json | ConvertFrom-Json | Format-Table

# Xem evidence riêng cho test case
Get-Content reports\evidence\TC02.stdout.txt
```

---

## 6. Troubleshooting

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `curl.exe: Connection refused` | Container chưa chạy | `docker compose up -d` rồi đợi 10s |
| 401 Unauthorized | Token sai | Sửa `authToken` trong environment = `local-dev-token-vision` |
| 422 Unprocessable Entity | Body sai schema | Xem docs/BAO_CAO_API.md để biết schema |
| postman CLI not found | Chưa cài | Download từ postman.com/downloads |
| newman: not found | Chưa cài | `npm install -g newman` |
| TC17 (Camera Stream mock) fail | Camera mock không chạy | Đảm bảo `http://192.168.137.115:8001/health` trả 200 |

---

## 7. Cleanup

```powershell
# Dừng container (giữ image)
docker compose down

# Xóa luôn image
docker compose down --rmi all

# Xóa evidence (optional)
Remove-Item -Recurse -Force reports\evidence\*
```

---

*Hướng dẫn chạy test — FIT4110 Buổi 5 — 2026-08-25*
