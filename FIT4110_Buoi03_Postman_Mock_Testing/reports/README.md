# Reports — Newman & Spectral evidence

Mỗi lần chạy `npm run test:vision:*` hoặc `npm run lint:vision`, file evidence được sinh/cập nhật tại đây.

## Cấu trúc file

| File | Mô tả | Được track trong git? |
|---|---|---|
| `vision-newman-report-mock.xml` | JUnit XML — kết quả Newman trên Prism mock | ❌ |
| `vision-newman-report-mock.html` | HTML report — Newman trên Prism mock | ❌ |
| `vision-newman-report-local.xml` | JUnit XML — Newman trên service thật (port 8000) | ❌ |
| `vision-newman-report-local.html` | HTML report — Newman trên service thật | ❌ |
| `vision-newman-report-data.xml` | Newman với iteration-data từ `mock-data/*.json` | ❌ |
| `contract-lint-vision.txt` | Spectral lint output cho `contracts/ai-vision.openapi.yaml` | ✅ (đã override .gitignore) |
| `contract-lint-report.txt` | Spectral lint cho tất cả contracts | ✅ |
| `req-detect.json`, `req-face.json` | Sample request body để test thủ công | ❌ |

## Cách chạy lại

```bash
# Trên Windows (PowerShell, đã activate env DichVuKetNoi)
npm run test:vision:mock     # chạy Newman trên Prism mock
npm run test:vision:local    # chạy Newman trên service thật (cần serve:vision đang chạy)
npm run test:vision:data     # chạy với iteration-data
npm run lint:vision          # Spectral lint contract
```

## Evidence gần nhất

- Mock env: **23 requests / 49 assertions / 0 failures** (file `.xml` đính kèm).
- Local env (service thật + side mocks 4012/4014): **23 requests / 49 assertions / 0 failures**.
- Spectral lint: **0 errors, 1 warning** (`info-contact` — không bắt buộc).

## Quy ước

- Không commit file `*.xml` / `*.html` — chúng được tạo lại mỗi lần chạy test.
- Khi nộp bài, đính kèm file HTML làm bằng chứng (hoặc link GitHub Actions artifact).
