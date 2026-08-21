# User Story — IoT Ingestion → Analytics

## 1. Cơ chế

**Queue async**

## 2. Bối cảnh

IoT Ingestion feed telemetry cho Analytics để aggregate theo giờ/ngày và hiển thị dashboard.

## 3. Nhu cầu của Consumer

Ở Lab 02 chỉ thống nhất event schema sơ bộ và khóa aggregate.

## 4. Endpoint / Event trọng tâm

- `Event telemetry.ingested`
- `Event device.status.changed`

## 5. Error case / Issue cần nghĩ trước

- Dữ liệu sai định dạng.
- Thiếu thông tin định danh hoặc correlation id.
- Consumer và Provider hiểu khác nhau về trạng thái nghiệp vụ.
- Trùng event/request hoặc retry gây xử lý lặp.
- Timeout hoặc lỗi downstream.

## 6. Câu hỏi gợi ý cho phiên đàm phán

1. Analytics aggregate theo deviceId hay zoneId?
2. Có cần batch event không?
3. Dữ liệu lỗi format được bỏ qua hay đưa vào dead-letter?

## 7. Ghi chú phạm vi Lab 02

Cặp này là Queue async. Trong Lab 02, hai bên chưa cần viết AsyncAPI đầy đủ. Tuy nhiên, cần ghi rõ thỏa thuận sơ bộ trong `negotiation-log.md` hoặc dùng `docs/event-contract-template.md` nếu giảng viên yêu cầu.
