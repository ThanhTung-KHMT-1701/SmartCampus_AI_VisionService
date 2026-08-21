# Hướng dẫn sinh viên — Lab 02 OpenAPI 3.1

**Học phần:** Dịch vụ kết nối và công nghệ nền tảng  
**Mã học phần:** FIT4110  
**Lab:** Lab 02 — Buổi 2/6  
**Case study:** Smart Campus Operations Platform  


---

## 1. Mục tiêu

Lab 02 là bước chuyển từ **ý tưởng/service boundary** sang **hợp đồng kỹ thuật**.

Trước Lab 02, nhóm đã có `service-boundary.md` từ Lab 01. Sau Lab 02, cặp đàm phán phải có:

- `openapi.yaml` đã thống nhất.
- `negotiation-log.md` làm biên bản ký kết.
- Báo cáo `spectral-report.txt`.
- Bằng chứng Prism mock server qua 5 request mẫu.

---

## 2. Chuẩn đầu ra của Lab 02

Sau buổi này, sinh viên có thể:

1. Viết tài liệu OpenAPI 3.1 mô tả hợp đồng REST API.
2. Dùng JSON Schema 2020-12 để định nghĩa dữ liệu, ràng buộc, kế thừa và polymorphism.
3. Đàm phán hợp đồng giữa hai vai Provider và Consumer trước khi code.
4. Kiểm thử hợp đồng bằng Spectral và Prism.
5. Lưu bằng chứng nghiệm thu trong repo GitHub.

---

## 3. Nguyên tắc cốt lõi

### 3.1. Contract-first

Không code trước khi thống nhất hợp đồng.

Hợp đồng của Lab 02 gồm:

```text
openapi.yaml
negotiation-log.md
```

Nếu nhóm tự code rồi mới viết tài liệu, tài liệu chỉ còn là mô tả ngược, không còn giá trị tích hợp.

### 3.2. Đàm phán thật

Phiên đàm phán không phải là thuyết trình. Hai bên phải đưa xung đột thật ra bàn:

- tên field;
- kiểu dữ liệu;
- content-type;
- mã lỗi;
- format id;
- giới hạn kích thước payload;
- trạng thái nghiệp vụ;
- pagination;
- versioning.

### 3.3. Cả cặp cùng chịu trách nhiệm

Lab 02 chấm theo cặp đàm phán. Chất lượng hợp đồng là kết quả chung của Provider và Consumer.

---

## 4. Đầu vào cần có trước buổi

Mỗi nhóm cần chuẩn bị:

- Service Boundary Diagram từ Lab 01.
- Danh sách endpoint dự kiến.
- Node.js LTS >= 20.
- Git và tài khoản GitHub.
- Spectral CLI.
- Prism CLI.
- Swagger Editor Online để soạn và xem trước tài liệu API.
- Đúng user story của cặp trong thư mục `user-stories/`.

> Lab 02 chưa yêu cầu Postman. Việc gọi thử mock server thực hiện bằng `curl` hoặc script có sẵn trong repo.

---

## 5. Đầu ra phải nộp

| Artefact | Vị trí trong repo | Bắt buộc |
|---|---|---|
| `openapi.yaml` đã ký | Thư mục gốc | Có |
| `negotiation-log.md` | Thư mục gốc | Có |
| `analysis-provider.md` | `docs/` | Có |
| `analysis-consumer.md` | `docs/` | Có |
| `spectral-report.txt` | `evidence/buoi-02/` | Có |
| 5 ảnh mock server | `evidence/buoi-02/mock-screenshots/` | Có |
| `VERSIONING.md` | Thư mục gốc | Có cho BTVN |

---

## 5A. Dependency Map 10 cặp

Smart Campus có **10 dependency** chính. Xem chi tiết trong:

```text
docs/pairing-matrix.md
```

Trong đó:

- REST sync: cặp **1, 2, 3, 10** — viết và validate bằng `openapi.yaml` trong Lab 02.
- Queue async: cặp **4, 5, 6, 7, 8, 9** — ghi nhận event contract sơ bộ, chuyển sang Lab 03 để đặc tả AsyncAPI/topic schema.

Điểm quan trọng: Lab 02 vẫn là bài **contract-first**, nhưng không ép Queue async thành REST nếu kiến trúc gốc là bất đồng bộ.

---

## 6. Tiến trình 250 phút

| Block | Thời lượng | Hoạt động chính | Đầu ra |
|---|---:|---|---|
| 0 | 15 phút | Khởi động chung về contract-first | Hiểu yêu cầu |
| 1 | 60 phút | OpenAPI 3.1, JSON Schema 2020-12, Spectral | Ghi chú cá nhân |
| 2 | 60 phút | Phân tích yêu cầu cặp + soạn bản thảo | `analysis-*.md`, `openapi.yaml` v0.9 |
| 3 | 70 phút | Đàm phán hợp đồng + validate bằng mock | `openapi.yaml` v1.0, `negotiation-log.md` |
| 4 | 30 phút | Review chéo giữa các cặp trong cùng sản phẩm | Bảng thống nhất naming |
| 5 | 15 phút | Chốt buổi và giao BTVN | Plan hoàn thiện |

---

## 7. Quy trình làm việc

### 7.1. Phân tích độc lập

Consumer và Provider điền riêng:

```text
docs/analysis-consumer.md
docs/analysis-provider.md
```

Mỗi bên cần có:

- resource chính;
- action/API dự kiến;
- tối thiểu 5 error case;
- tối thiểu 3 câu hỏi cho bên còn lại;
- giả định bổ sung nếu user story chưa rõ.

---

### 7.2. Soạn thảo OpenAPI 3.1 bằng Swagger Editor Online

Công cụ chính của buổi này là:

```text
https://editor.swagger.io
```

Cách làm:

1. Mở file `openapi.yaml` trong repo.
2. Copy nội dung YAML và dán vào Swagger Editor Online.
3. Sửa path, operation, schema, example theo cặp đàm phán.
4. Theo dõi preview bên phải để kiểm tra tài liệu có đọc được không.
5. Sau khi thống nhất, copy YAML về lại `openapi.yaml`.
6. Chạy Spectral để kiểm tra rule của lớp.

Lưu ý: Swagger Editor Online chỉ giúp soạn thảo và kiểm tra cú pháp/preview. File vẫn phải pass `campus-spectral.yaml`.

File chính:

```text
openapi.yaml
```

Yêu cầu tối thiểu:

- `openapi: 3.1.0`
- tối thiểu 4 path;
- operation có `operationId`, `summary`, `description`, `tags`;
- đủ status code phù hợp: `200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`, `422`, `500` nếu hợp lý;
- schema tách vào `components/schemas`;
- có `oneOf` + `discriminator`;
- có union type với `null`;
- response lỗi dùng `application/problem+json`.

---

### 7.3. Đàm phán hợp đồng

Hai bên ghi issue trong:

```text
negotiation-log.md
```

Mỗi issue nên có cấu trúc:

```text
- Raised by:
- Endpoint:
- Concern:
- Proposal:
- Resolution:
- Rationale:
- Impact:
```

Tối thiểu 6 issue cho cả phiên.

---

### 7.4. Validate hợp đồng

Chạy:

```bash
spectral lint openapi.yaml --ruleset campus-spectral.yaml
```

Xuất report:

```bash
spectral lint openapi.yaml --ruleset campus-spectral.yaml --format text > evidence/buoi-02/spectral-report.txt
```

Chạy mock:

```bash
prism mock openapi.yaml --port 4010
```

Test 5 request mẫu bằng `curl`, không dùng Postman trong Lab 02:

- 3 happy path;
- 2 error case.

Có thể dùng script:

```bash
./scripts/test_mock_with_curl.sh
```

Windows:

```powershell
.\scripts\test_mock_with_curl.ps1
```

Mỗi request lưu ảnh vào:

```text
evidence/buoi-02/mock-screenshots/
```

---

## 8. Bài tập về nhà trước Lab 03

Hoàn thiện 3 phần:

1. **Webhook:** định nghĩa ít nhất 1 webhook trong block `webhooks`.
2. **Cursor-based pagination:** áp dụng cho ít nhất 2 endpoint GET trả về danh sách.
3. **Versioning:** hoàn thiện `VERSIONING.md`, nêu backward-compatible change, breaking change, `deprecated: true`, `Sunset` header.

---

## 9. Checklist cuối buổi

Trước khi rời phòng, cặp đàm phán kiểm tra:

- [ ] `openapi.yaml` dùng OpenAPI 3.1.0.
- [ ] `openapi.yaml` pass Spectral, không có severity error.
- [ ] `negotiation-log.md` có tối thiểu 6 issue.
- [ ] Có chữ ký Provider, Consumer, Witness.
- [ ] Có `analysis-provider.md`.
- [ ] Có `analysis-consumer.md`.
- [ ] Có `spectral-report.txt`.
- [ ] Có 5 ảnh mock server.
- [ ] Có commit cuối theo mẫu `chore(contract): <cap> v1.0 signed-off`.
- [ ] `README.md` mô tả được cách chạy mock.

---

## 10. Câu hỏi thường gặp

### Có bắt buộc dùng Stoplight Studio hoặc Postman không?

Không. Lab 02 ưu tiên **Swagger Editor Online** để soạn `openapi.yaml`. Postman chưa dùng ở buổi này; mock server được kiểm thử bằng `curl` để sinh viên tập trung vào hợp đồng API, schema và đàm phán.

### Có được tự suy diễn user story không?

Được, nhưng phải ghi rõ ở mục giả định trong `analysis-*.md` và đưa ra bàn đàm phán.

### Nếu hai bên không thống nhất thì sao?

Ghi cả hai phương án vào `negotiation-log.md`, gọi GV/TA làm trọng tài và chốt phương án cuối.

### Có được dùng MQTT/AMQP/RTSP trong Lab 02 không?

Lab 02 tập trung vào REST API bằng OpenAPI. Giao thức sự kiện hoặc streaming có thể để sang lab sau.
