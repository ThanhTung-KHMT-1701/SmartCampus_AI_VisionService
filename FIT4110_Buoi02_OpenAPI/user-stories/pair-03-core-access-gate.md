# User Story — Core Business → Access Gate

## 1. Cơ chế

**REST sync**

## 2. Bối cảnh

Core Business cần truy xuất log quẹt thẻ, trạng thái gate hoặc thông tin card từ Access Gate để kiểm tra/audit.

## 3. Nhu cầu của Consumer

Consumer cần dữ liệu access log có cardId, gateId, direction, timestamp, status và operator note nếu có.

## 4. Endpoint / Event trọng tâm

- `GET /access/logs/recent`
- `GET /access/logs/{logId}`
- `GET /gates/{gateId}/status`
- `GET /cards/{cardId}`

## 5. Error case / Issue cần nghĩ trước

- Dữ liệu sai định dạng.
- Thiếu thông tin định danh hoặc correlation id.
- Consumer và Provider hiểu khác nhau về trạng thái nghiệp vụ.
- Trùng event/request hoặc retry gây xử lý lặp.
- Timeout hoặc lỗi downstream.

## 6. Câu hỏi gợi ý cho phiên đàm phán

1. Log lưu ở Access Gate bao lâu?
2. Core có được query theo khoảng thời gian không?
3. Card bị khóa thì Access Gate trả trạng thái nào?

## 7. Ghi chú phạm vi Lab 02

Cặp này là REST sync. Hai bên cần viết hoặc chỉnh `openapi.yaml`, chạy Spectral lint và chạy Prism mock server để tạo bằng chứng.
