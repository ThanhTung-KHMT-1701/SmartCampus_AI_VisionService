# Rubric chấm điểm — FIT4110 Lab 02 OpenAPI 3.1 Contract-First

## 1. Phạm vi áp dụng

Rubric này dùng để chấm **Lab 02 — Thực hành đàm phán và viết hợp đồng API**.

Lab 02 có hai loại cặp phụ thuộc trong Dependency Map:

- **REST sync pairs**: chấm theo Rubric A. Sinh viên phải viết `openapi.yaml`, chạy Spectral, dựng Prism mock server và test bằng `curl`.
- **Queue async pairs**: chấm theo Rubric B. Sinh viên chưa cần viết AsyncAPI đầy đủ trong Lab 02, nhưng phải tạo event contract sơ bộ để chuẩn bị cho Lab 03.

> Nguyên tắc chung: chấm theo **artefact có thể kiểm chứng trong repo**, không chấm theo lời trình bày miệng nếu không có minh chứng đi kèm.

---

## 2. Rubric A — REST sync pair, 10 điểm

Áp dụng cho các cặp REST sync trong `docs/pairing-matrix.md`, ví dụ:

- Pair 01: Camera Stream → AI Vision
- Pair 02: Core Business → AI Vision
- Pair 03: Core Business → Access Gate
- Pair 10: Access Gate → Core Business

| Tiêu chí | Trọng số | Xuất sắc | Đạt | Chưa đạt | Minh chứng bắt buộc |
|---|---:|---|---|---|---|
| A1. Tính hợp lệ OpenAPI 3.1 | 1.5 | `openapi.yaml` dùng đúng `openapi: 3.1.0`, cấu trúc rõ, pass Spectral không có `error`; chỉ còn warning nhỏ có giải thích | Có OpenAPI 3.1, chạy được Spectral, còn một vài warning chưa giải thích rõ | Dùng OpenAPI 3.0.x, YAML lỗi, hoặc Spectral có `error` | `openapi.yaml`, `evidence/buoi-02/spectral-report.txt` |
| A2. Độ phủ nghiệp vụ và endpoint | 2.0 | Có ít nhất 4 path đúng user story, method hợp lý, path resource-oriented, đủ happy path và error path chính | Có endpoint chính nhưng còn thiếu một vài path phụ hoặc status code | Endpoint không khớp user story, đặt path kiểu động từ, thiếu nhiều status code | `openapi.yaml`, `docs/analysis-*.md` |
| A3. Chất lượng schema và JSON Schema 2020-12 | 2.5 | Schema tách vào `components/schemas`, dùng `$ref`, có constraint phù hợp, có `oneOf/discriminator`, có union type với `null`, có `additionalProperties: false` ở object quan trọng | Schema cơ bản đúng nhưng constraint chưa đầy đủ hoặc dùng `$ref` chưa nhất quán | Inline schema dài, thiếu required/constraint, không thể hiện đặc trưng OpenAPI 3.1 | `openapi.yaml` |
| A4. Error model và response | 1.0 | Response 4xx/5xx dùng Problem Details, có ví dụ, status code hợp lý: 400/401/403/404/409/422/500 | Có error response nhưng chưa thống nhất Problem Details hoặc thiếu example | Error response sơ sài, dùng chung một response không rõ nghĩa | `openapi.yaml` |
| A5. Chất lượng đàm phán hợp đồng | 2.0 | `negotiation-log.md` có ít nhất 6 issue, mỗi issue có concern, proposal, resolution, rationale, impact; có sign-off Provider/Consumer/Witness | Có đủ issue nhưng rationale/impact còn ngắn hoặc một vài issue chưa cụ thể | Thiếu issue, chỉ ghi chung chung, không có sign-off | `negotiation-log.md` |
| A6. Mock server và minh chứng test | 1.0 | Prism chạy được, có 5 request bằng `curl`: 3 happy path + 2 error case; ảnh/log rõ status code và body | Mock chạy được nhưng minh chứng thiếu 1–2 request hoặc ảnh chưa rõ | Không dựng được mock hoặc không có minh chứng test | `evidence/buoi-02/mock-screenshots/`, script/log nếu có |

### Quy đổi nhanh Rubric A

| Mức | Khoảng điểm | Diễn giải |
|---|---:|---|
| A | 8.5–10.0 | Hợp đồng có thể dùng làm nền cho code Buổi 3 |
| B | 7.0–8.4 | Hợp đồng dùng được nhưng cần chỉnh schema/error/evidence |
| C | 5.0–6.9 | Có sản phẩm nhưng còn thiếu alignment hoặc validation |
| D | < 5.0 | Chưa đạt yêu cầu contract-first |

---

## 3. Rubric B — Queue async pair, 10 điểm

Áp dụng cho các cặp Queue async trong `docs/pairing-matrix.md`, ví dụ:

- Pair 04: Core Business → Notification
- Pair 05: IoT Ingestion → Core Business
- Pair 06: IoT Ingestion → Analytics
- Pair 07: Camera Stream → Analytics
- Pair 08: Core Business → Analytics
- Pair 09: Access Gate → Analytics

Trong Lab 02, các cặp này **chưa cần viết AsyncAPI đầy đủ**. Mục tiêu là tạo event contract sơ bộ để sang Lab 03 phát triển tiếp.

| Tiêu chí | Trọng số | Xuất sắc | Đạt | Chưa đạt | Minh chứng bắt buộc |
|---|---:|---|---|---|---|
| B1. Xác định event và vai trò Producer/Consumer | 2.0 | Nêu rõ event name, producer, consumer, trigger, mục đích nghiệp vụ và điều kiện phát event | Có event chính nhưng trigger hoặc vai trò còn mơ hồ | Không xác định được event hoặc nhầm producer/consumer | `docs/event-contract-template.md` hoặc file event contract riêng |
| B2. Payload schema sơ bộ | 2.5 | Payload có field bắt buộc/tùy chọn, kiểu dữ liệu, constraint, ví dụ JSON; nêu rõ timestamp, id, correlationId/requestId | Có payload nhưng thiếu constraint hoặc example chưa đầy đủ | Payload chỉ mô tả bằng lời, không có schema/example | Event contract file, `docs/analysis-*.md` |
| B3. Error/edge case và delivery concern | 1.5 | Có ít nhất 5 tình huống: duplicate, out-of-order, missing field, invalid schema, retry/dead-letter; nêu cách xử lý sơ bộ | Có một số edge case nhưng chưa gắn với cơ chế queue | Không xét lỗi/delivery concern | Event contract file, `negotiation-log.md` |
| B4. Chất lượng đàm phán | 2.0 | Có ít nhất 6 issue, trong đó có issue về event name, payload field, retry, ordering, idempotency, retention; có rationale và impact | Có issue nhưng còn chung chung hoặc thiếu impact | Không có biên bản đàm phán rõ ràng | `negotiation-log.md` |
| B5. Tính sẵn sàng cho Lab 03 | 1.0 | Event contract đủ tốt để chuyển sang AsyncAPI/topic schema ở Lab 03; nêu topic name dự kiến và broker giả định | Có hướng chuyển tiếp nhưng topic/broker chưa rõ | Không thể dùng làm đầu vào cho Lab 03 | Event contract file |
| B6. Repo/evidence và trình bày | 1.0 | File đặt đúng chỗ, commit rõ, checklist đủ; đại diện nhóm giải thích được 2 quyết định thiết kế | Có file nhưng sắp xếp hoặc commit chưa chuẩn | Thiếu evidence hoặc repo lộn xộn | `evidence/buoi-02/`, git log |

### Quy đổi nhanh Rubric B

| Mức | Khoảng điểm | Diễn giải |
|---|---:|---|
| A | 8.5–10 | Event contract rõ, đủ làm đầu vào Lab 03 |
| B | 7.0–8.4 | Có event contract dùng được nhưng cần bổ sung edge case/schema |
| C | 5.0–6.9 | Có hướng mô tả nhưng thiếu tính kỹ thuật |
| D | < 5.0 | Chưa đạt yêu cầu contract-first cho luồng async |

---


