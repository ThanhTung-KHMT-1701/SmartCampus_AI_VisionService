# Reports — Newman evidence for FIT4110 Lab05

Mỗi lần chạy `.\scripts\collect-evidence.ps1` hoặc `.\scripts\run-18-test-cases.ps1`, evidence được sinh tại đây.

## Cấu trúc file

| File | Mô tả | Git-tracked? |
|---|---|---|
| `vision-newman-report-docker-*.html` | Newman HTML report — Docker service thật | ❌ |
| `vision-newman-report-docker-*.xml`  | Newman JUnit XML — Docker service thật | ❌ |
| `vision-newman-report-docker-latest.html` | Alias → bản mới nhất | ❌ |
| `vision-newman-report-docker-latest.xml`  | Alias → bản mới nhất | ❌ |
| `vision-contract-smoke-*.txt` | contract-smoke.ps1 stdout output | ❌ |
| `evidence/` | Thư mục chứa stdout/body per test case | ❌ |
| `evidence/*.stdout.txt` | Raw output của từng test case (run-18-test-cases.ps1) | ❌ |
| `evidence/*.body.json` | Request body của từng test case | ❌ |
| `evidence/results.json` | Tổng hợp kết quả 18 test cases | ❌ |

## Cách chạy lại

```powershell
# 1. Smoke test nhanh (14 requests, dùng Invoke-WebRequest)
.\scripts\contract-smoke.ps1

# 2. 18 test cases đầy đủ với Postman CLI + evidence per case
.\scripts\run-18-test-cases.ps1

# 3. Newman với HTML/JUnit report (cần newman CLI)
.\scripts\collect-evidence.ps1
```

## Evidence gần nhất

Khi chạy xong, kiểm tra:

```powershell
# Kiểm tra container đang chạy chưa
docker compose ps

# Chạy smoke test
.\scripts\contract-smoke.ps1

# Chạy 18 test cases
.\scripts\run-18-test-cases.ps1

# Mở HTML report
Start-Process reports\vision-newman-report-docker-latest.html
```

## Di chuyển evidence sang máy khác (nộp bài)

Các file `*.html` và `evidence/*.txt` là bằng chứng chạy API thật trên Docker. Nén lại:

```powershell
Compress-Archive -Path reports -DestinationPath lab05-evidence.zip
```

## Ghi chú quan trọng

- Các file `*.html` / `*.xml` / `*.txt` trong `reports/` **KHÔNG** được commit vào git.
- Chỉ commit các file `.gitkeep` trong thư mục rỗng để giữ cấu trúc.
- Thư mục `evidence/` chứa bằng chứng chi tiết từng test case.
