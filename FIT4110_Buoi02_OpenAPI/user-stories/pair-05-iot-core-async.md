# User Story — IoT Ingestion → Core Business

## 1. Cơ chế

**Queue async**

## 2. Bối cảnh

IoT Ingestion publish sensor event mới để Core Business đánh giá policy hoặc phát hiện bất thường.

## 3. Nhu cầu của Consumer

Ở Lab 02 chỉ thống nhất event payload tối thiểu gồm deviceId, sensorType, value, unit, timestamp.

## 4. Endpoint / Event trọng tâm

- `Event sensor.reading.created`
- `Event sensor.threshold.exceeded`

## 5. Error case / Issue cần nghĩ trước

- Dữ liệu sai định dạng.
- Thiếu thông tin định danh hoặc correlation id.
- Consumer và Provider hiểu khác nhau về trạng thái nghiệp vụ.
- Trùng event/request hoặc retry gây xử lý lặp.
- Timeout hoặc lỗi downstream.

## 6. Câu hỏi gợi ý cho phiên đàm phán

1. Giá trị sensor dùng đơn vị nào?
2. Event có cần locationId không?
3. Core xử lý event trễ quá bao lâu thì bỏ qua?

## 7. Ghi chú phạm vi Lab 02

Cặp này là Queue async. Trong Lab 02, hai bên chưa cần viết AsyncAPI đầy đủ. Tuy nhiên, cần ghi rõ thỏa thuận sơ bộ trong `negotiation-log.md` hoặc dùng `docs/event-contract-template.md` nếu giảng viên yêu cầu.
