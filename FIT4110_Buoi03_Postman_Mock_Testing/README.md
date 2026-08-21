# FIT4110_lab03_postman_mock_testing

**Học phần:** FIT4110 – Dịch vụ kết nối và Công nghệ nền tảng  
**Buổi 3:** Kiểm thử tích hợp với Postman + Mock Server  
**Case study:** Smart Campus Operations Platform  

## Nội dung chính

Ở Lab 02, mỗi nhóm đã thiết kế `openapi.yaml` như một **hợp đồng API** giữa các service.

Trong Lab 03, hợp đồng đó sẽ được chuyển thành **bộ kiểm thử có thể chạy được** bằng Postman, Mock Server, Newman và CI.

> API contract không chỉ để đọc. API contract phải kiểm chứng được bằng test.

---

## 1. Bối cảnh bài lab

Trong một hệ thống nhiều service, không phải nhóm nào cũng hoàn thành code cùng lúc.

Ví dụ:

- Nhóm Camera cần gọi AI Vision, nhưng AI Vision chưa code xong.
- Nhóm Analytics cần dữ liệu từ IoT, Camera, Core, nhưng các service chưa sẵn sàng.
- Nhóm Core cần kiểm thử dữ liệu từ Access Gate, AI Vision, IoT, nhưng không thể chờ toàn bộ hệ thống hoàn chỉnh.

Cách xử lý là dùng:

```text
OpenAPI Contract → Mock Server → Postman Test → Newman Report → CI Evidence
```

Luồng làm việc:

1. Provider định nghĩa API bằng `openapi.yaml`.
2. Provider tạo mock server từ OpenAPI contract.
3. Consumer gọi mock server để phát triển và kiểm thử sớm.
4. Nhóm viết Postman Collection để kiểm tra API của mình.
5. Newman chạy collection trên terminal hoặc GitHub Actions.
6. Contract được lint trước khi chạy test.
7. Cùng một collection được chạy trên 2 môi trường:
   - `mock`: kiểm thử theo contract khi service thật chưa hoàn thiện.
   - `local`: kiểm thử service thật khi nhóm đã code xong.

---

## 2. Mục tiêu sau buổi lab

Sau khi hoàn thành lab này, mỗi nhóm cần làm được các việc sau:

- Import OpenAPI vào Postman.
- Tạo Postman Collection có cấu trúc rõ ràng.
- Chạy Mock Server từ OpenAPI contract.
- Viết test script bằng `pm.test`.
- Kiểm tra status code, response body, schema cơ bản, auth, negative case và boundary case.
- Tạo environment `mock` và `local`.
- Không hardcode URL hoặc token trong collection.
- Chạy collection bằng Newman.
- Xuất report làm bằng chứng.
- Viết consumer-side smoke test với mock của service phụ thuộc.
- Chạy contract lint và Newman trong CI.

---

## 3. Cấu trúc repo

```text
FIT4110_lab03_postman_mock_testing/
├── README.md
├── package.json
├── Makefile
├── contracts/
│   ├── iot-ingestion.openapi.yaml
│   └── ai-vision.openapi.yaml
├── postman/
│   ├── collections/
│   │   └── FIT4110_lab03_iot_ingestion.postman_collection.json
│   └── environments/
│       ├── FIT4110_lab03_mock.postman_environment.json
│       └── FIT4110_lab03_local.postman_environment.json
├── mock-data/
│   ├── sensor-reading-valid.json
│   ├── sensor-reading-invalid-missing-device.json
│   └── sensor-reading-boundary.json
├── docs/
│   ├── TEAM_TASKS.md
│   ├── CONSUMER_SIDE_TESTING.md
│   └── GITHUB_ACTIONS_GUIDE.md
├── checklists/
│   ├── reliability_checklist.md
│   └── submission_checklist.md
├── templates/
│   ├── test-case-matrix.csv
│   └── consumer-provider-handshake.md
├── scripts/
│   ├── start-prism-mock.sh
│   └── run-newman.sh
├── reports/
│   └── .gitkeep
└── .github/
    └── workflows/
        └── newman.yml
```

---

## 4. Chuẩn bị môi trường

Cần cài trước:

- Node.js 20.x LTS
- npm
- Git
- Postman Desktop hoặc Postman Web

Cài dependencies:

```bash
npm install
```

Kiểm tra version:

```bash
node --version
npx newman --version
npx prism --version
```

---

## 5. Quy định về Postman Environment

Collection không được hardcode:

- `baseUrl`
- `authToken`
- URL mock của service khác

Tất cả các giá trị này phải đặt trong Postman Environment.

### Biến môi trường bắt buộc

| Biến | Mock environment | Local environment | Ý nghĩa |
|---|---|---|---|
| `env` | `mock` | `local` | Môi trường đang chạy test |
| `baseUrl` | `http://localhost:4010` | `http://localhost:8000` | URL service chính |
| `authToken` | `lab-token` | `local-dev-token` | Token hoặc API key |
| `teamName` | `team-iot` | `team-iot` | Tên nhóm hoặc tên service |
| `aiVisionMockUrl` | `http://localhost:4011` | `http://localhost:4011` | URL mock của service phụ thuộc |

Ví dụ URL trong Postman:

```text
{{baseUrl}}/readings
```

Ví dụ Authorization header:

```text
Authorization: Bearer {{authToken}}
```

---

## 6. Chạy Mock Server

Contract mẫu của IoT Ingestion nằm tại:

```text
contracts/iot-ingestion.openapi.yaml
```

Chạy mock IoT:

```bash
npm run mock:iot
```

Mock server mặc định chạy tại:

```text
http://localhost:4010
```

Kiểm tra mock server:

```bash
curl http://localhost:4010/health
```

Nếu cần chạy mock AI Vision cho consumer-side smoke test:

```bash
npm run mock:vision
```

Mock AI Vision có thể chạy tại:

```text
http://localhost:4011
```

---

## 7. Lưu ý về Prism Mock Server

Prism Mock Server giúp kiểm thử sớm khi service thật chưa hoàn thiện.

Tuy nhiên, cần phân biệt rõ:

| Mock Server | Service thật |
|---|---|
| Trả response theo OpenAPI example | Chạy logic thật |
| Có thể mô phỏng status code | Tự xử lý nghiệp vụ |
| Không kiểm chứng database thật | Có database thật |
| Không chứng minh auth thật | Có auth thật |
| Không dùng để đo latency thật | Có thể kiểm thử hiệu năng cơ bản |

### Không dùng `Prefer: code=401` để chứng minh auth

Header `Prefer: code=XXX` là tính năng hỗ trợ mock response của Prism. Đây không phải cách kiểm thử HTTP chuẩn với service thật.

Auth test đúng cần gửi request thật sự thiếu token hoặc sai token.

Ví dụ test:

```javascript
pm.test("Unauthorized request returns 401 or 403", function () {
  pm.expect([401, 403]).to.include(pm.response.code);
});
```

Nếu mock trả `200` cho request thiếu token, test nên fail. Điều này cho thấy mock chưa kiểm tra auth thật.

---

## 8. Chạy Postman Collection bằng Newman

Chạy với mock environment:

```bash
npm run test:mock
```

Chạy với local environment:

```bash
npm run test:local
```

Report sẽ được xuất vào thư mục:

```text
reports/
```

Ví dụ chạy Newman trực tiếp:

```bash
npx newman run postman/collections/FIT4110_lab03_iot_ingestion.postman_collection.json \
  -e postman/environments/FIT4110_lab03_mock.postman_environment.json \
  -r cli,junit,htmlextra \
  --reporter-junit-export reports/newman-report.xml \
  --reporter-htmlextra-export reports/newman-report.html
```

---

## 9. Cấu trúc Postman Collection

Mỗi collection cần có các folder sau:

```text
01_Functional
02_Auth
03_Negative
04_Boundary_Reliability
05_Consumer_side_Smoke
06_Local_only_NonFunctional
```

---

### 9.1 Functional

Kiểm thử các luồng hợp lệ.

Ví dụ:

```javascript
pm.test("Status code is 201", function () {
  pm.response.to.have.status(201);
});

pm.test("Response has readingId", function () {
  const json = pm.response.json();
  pm.expect(json).to.have.property("readingId");
});
```

---

### 9.2 Auth

Kiểm thử:

- Request có token hợp lệ.
- Request thiếu token.
- Request có token sai.

Không ép mock trả `401` bằng `Prefer: code=401` rồi xem đó là auth test thật.

---

### 9.3 Negative

Kiểm thử dữ liệu sai:

- Thiếu field bắt buộc.
- Sai kiểu dữ liệu.
- Sai query parameter.
- Payload không hợp lệ.

Ví dụ:

```javascript
pm.test("Invalid payload returns client error", function () {
  pm.expect([400, 422]).to.include(pm.response.code);
});

pm.test("Error response follows ProblemDetails", function () {
  const json = pm.response.json();
  pm.expect(json).to.have.property("status");
  pm.expect(json.status).to.be.within(400, 599);
});
```

---

### 9.4 Boundary / Reliability

Không viết test chỉ kiểm tra lại request body đã gửi.

Ví dụ không đạt:

```javascript
pm.test("Boundary behavior is documented", function () {
  pm.expect(pm.request.body.raw).to.include("80");
});
```

Test boundary cần kiểm tra response từ server.

Ví dụ:

```javascript
pm.test("High temperature is accepted with warning or rejected as invalid", function () {
  pm.expect([201, 400, 422]).to.include(pm.response.code);

  if (pm.response.code === 201) {
    pm.expect(pm.response.headers.has("X-Warning")).to.equal(true);
  }

  if ([400, 422].includes(pm.response.code)) {
    const json = pm.response.json();
    pm.expect(json).to.have.property("detail");
  }
});
```

---

### 9.5 Consumer-side Smoke

Consumer-side smoke test dùng để kiểm tra một service có thể gọi được contract tối thiểu của service phụ thuộc.

Ví dụ IoT cần gọi mock của AI Vision:

```text
POST {{aiVisionMockUrl}}/detect
```

Consumer-side test không nên chỉ gọi lại API của chính service mình.

---

### 9.6 Local-only NonFunctional

Các test về latency hoặc SLA chỉ nên chạy với service thật.

Ví dụ:

```javascript
if (pm.environment.get("env") === "local") {
  pm.test("Response time is below 1000ms on local service", function () {
    pm.expect(pm.response.responseTime).to.be.below(1000);
  });
}
```

Không dùng latency của mock server để kết luận service thật nhanh hay chậm.

---

## 10. Quy trình làm bài

Thực hiện theo thứ tự sau:

1. Đọc lại contract `openapi.yaml` từ Lab 02.
2. Chạy contract lint bằng Spectral hoặc Redocly.
3. Import OpenAPI vào Postman.
4. Tạo collection theo các folder bắt buộc.
5. Tạo environment `mock`.
6. Chạy Prism Mock Server.
7. Chạy collection với Newman trên mock.
8. Tạo environment `local`.
9. Chạy lại collection trên service thật.
10. Viết consumer-side smoke test với mock của ít nhất một service phụ thuộc.
11. Xuất Newman report.
12. Hoàn thiện test-case matrix.
13. Hoàn thiện reliability checklist.
14. Hoàn thiện consumer-provider handshake.

---

## 11. Yêu cầu tối thiểu theo nhóm

Mỗi nhóm thay contract mẫu bằng contract của service mình từ Lab 02, sau đó tạo bộ test tương ứng.

| Nhóm | Số test tối thiểu | Bắt buộc có |
|---|---:|---|
| `team-iot` | 10 | POST reading, latest reading, auth, validation, boundary, rate limit |
| `team-camera` | 10 | upload frame, trigger analyze, invalid image, callback/mock AI Vision |
| `team-gate` | 10 | access event, allow/deny, invalid card, auth |
| `team-vision` | 10 | detect image, model info, invalid image_url/base64, confidence boundary |
| `team-analytics` | 10 | ingest event, aggregate metric, missing time range, multi-source smoke |
| `team-core` | 10 | evaluate sensor/access/detection, policy not found, alert creation |
| `team-notify` | 10 | send notification, retry, dedupe, invalid channel, upstream alert mock |

Một request có thể có nhiều `pm.test`, nhưng phần đánh giá tập trung vào ý nghĩa kiểm thử, không chỉ đếm số assertion.

---

## 12. Yêu cầu OpenAPI Contract

Contract của mỗi nhóm cần đảm bảo:

- Mỗi operation có ít nhất một response thành công `2xx`.
- Mỗi operation có ít nhất một response lỗi `4xx`.
- Query parameter có `minimum`, `maximum`, `enum` hoặc `pattern` khi phù hợp.
- Error response dùng cấu trúc tương thích `ProblemDetails`.
- `ProblemDetails.status` có `minimum: 400` và `maximum: 599`.
- API có nguy cơ bị gọi quá nhiều nên cân nhắc response `429 Too Many Requests`.
- Các field dạng enum nghiệp vụ phải được ràng buộc rõ.

Ví dụ:

```yaml
metric:
  type: string
  enum: [temperature, humidity, motion, smoke]

unit:
  type: string
  enum: [celsius, percent, boolean, ppm]
```

Ví dụ `ProblemDetails`:

```yaml
ProblemDetails:
  type: object
  required: [type, title, status]
  properties:
    type:
      type: string
    title:
      type: string
    status:
      type: integer
      minimum: 400
      maximum: 599
    detail:
      type: string
```

---

## 13. Data-driven Testing

Các file trong `mock-data/` nên được dùng cho test, không chỉ để tham khảo.

Ví dụ chạy Newman với data file:

```bash
npx newman run postman/collections/FIT4110_lab03_iot_ingestion.postman_collection.json \
  -e postman/environments/FIT4110_lab03_mock.postman_environment.json \
  --iteration-data mock-data/sensor-reading-valid.json
```

Nếu collection nhúng JSON trực tiếp trong `body.raw`, cần đảm bảo `test-case-matrix.csv` mô tả đúng dữ liệu được dùng trong collection.

---

## 14. GitHub Actions

CI nên chạy theo thứ tự:

1. Install dependencies.
2. Lint OpenAPI contract.
3. Start Prism mock server.
4. Wait until mock server is ready.
5. Run Newman.
6. Upload report artifact.

Ví dụ workflow:

```yaml
name: Contract and Newman Tests

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Lint OpenAPI contracts
        run: npx @stoplight/spectral-cli lint contracts/*.yaml

      - name: Start Prism mock server
        run: nohup npm run mock:iot > prism.log 2>&1 &

      - name: Wait for mock server
        run: npx wait-on http://localhost:4010/health --timeout 30000

      - name: Run Newman on mock environment
        run: npm run test:mock

      - name: Show Prism log on failure
        if: failure()
        run: cat prism.log || true

      - name: Upload Newman reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: newman-reports
          path: reports/
```

Không nên chỉ dùng `sleep 5` để đợi mock server vì mock có thể chưa sẵn sàng.

---

## 15. Sản phẩm cần nộp

Mỗi nhóm cần nộp các file sau:

```text
contracts/<team>.openapi.yaml
postman/collections/<team>.postman_collection.json
postman/environments/<team>_mock.postman_environment.json
postman/environments/<team>_local.postman_environment.json
reports/newman-report.xml
reports/newman-report.html
reports/contract-lint-report.txt
checklists/reliability_checklist.md
templates/test-case-matrix.csv
templates/consumer-provider-handshake.md
```

Ngoài ra cần có một trong các bằng chứng sau:

- Link GitHub Actions run.
- Ảnh chụp terminal chạy Newman.
- Log CLI chứng minh test đã chạy.
- Report HTML/XML trong thư mục `reports/`.

---

## 16. Điều kiện hoàn thành

Một nhóm được xem là hoàn thành Lab 03 khi:

- Contract lint pass hoặc có giải thích rõ warning còn lại.
- Collection chạy được trên mock environment.
- Collection chạy được trên local environment, hoặc có ghi chú rõ phần chưa hoàn thiện.
- Collection không hardcode `baseUrl` hoặc `authToken`.
- Có test cho happy path, auth, negative, boundary/reliability.
- Có ít nhất một consumer-side smoke test gọi mock của service phụ thuộc.
- Newman report được sinh trong thư mục `reports/`.
- Test-case matrix map được từng test với endpoint, input, expected status và loại test.
- Reliability checklist đã hoàn thiện.
- Consumer-provider handshake đã hoàn thiện.

---

## 17. Rubric đánh giá

| Tiêu chí | Điểm | Mô tả đạt tối đa |
|---|---:|---|
| OpenAPI contract | 1.5 | Contract lint pass, schema rõ, có response lỗi, có enum/range phù hợp |
| Cấu trúc collection | 1.5 | Có đủ folder Functional/Auth/Negative/Boundary/Consumer-side/Local-only, request đặt tên rõ |
| Test coverage | 2.5 | Có happy path, auth, validation error, boundary, response body/schema |
| Mock và local environment | 1.5 | Cùng một collection chạy được trên mock và local, không hardcode URL/token |
| Newman report và CI evidence | 1.5 | Có report XML/HTML, có log hoặc GitHub Actions chạy contract lint + Newman |
| Consumer-side smoke test | 1.0 | Có test gọi mock của ít nhất một service phụ thuộc và có handshake |
| Checklist và test-case matrix | 0.5 | Điền đủ reliability checklist và test-case matrix |
| **Tổng** | **10.0** | |

---

## 18. Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `ECONNREFUSED` | Mock server chưa chạy | Chạy `npm run mock:iot` và kiểm tra `/health` |
| Newman chạy vào mock dù muốn test local | Environment local chưa được load hoặc collection còn hardcode `baseUrl` | Kiểm tra tham số `-e` và collection variables |
| `401 Unauthorized` ở happy path | Thiếu hoặc sai `authToken` | Kiểm tra environment và Authorization header |
| Auth test pass trên mock nhưng fail trên local | Mock không validate auth thật | Chạy lại với service thật và điều chỉnh test |
| Test pass trên mock nhưng fail trên local | Service thật chưa đúng contract | So sánh response với OpenAPI |
| Boundary test không có ý nghĩa | Test đang kiểm request body thay vì response | Assert status code, error body, warning header hoặc business rule |
| CI fail vì port 4010 bận | Mock process cũ chưa cleanup | Cleanup process hoặc đổi port |
| Spectral lint fail | Contract thiếu response lỗi hoặc schema thiếu ràng buộc | Sửa OpenAPI trước khi chạy Newman |

---

## 19. Gợi ý `.gitignore`

```gitignore
node_modules/
.env
.DS_Store
prism.log
reports/*.xml
reports/*.html
reports/*.json
!reports/.gitkeep
```

---

## 20. Tinh thần của buổi học

Sau Buổi 2, nhóm đã có **hợp đồng API**.

Sau Buổi 3, nhóm cần có **bộ kiểm thử có bằng chứng chạy được**.

Mỗi lần sửa service, nhóm cần chứng minh được:

- API vẫn đúng contract.
- Consumer vẫn gọi được.
- Lỗi được xử lý có kiểm soát.
- Report có thể chạy lại bằng Newman hoặc GitHub Actions.
