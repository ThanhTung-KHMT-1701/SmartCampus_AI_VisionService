# User Story — Access Gate → Core Business

## 1. Cơ chế

**REST sync**

## 2. Bối cảnh

Access Gate gọi Core Business realtime để kiểm tra policy ra/vào trước khi mở cổng.

## 3. Nhu cầu của Consumer

Consumer cần response rất nhanh gồm allow/deny, reasonCode, policyId và expiresAt để tránh kẹt cổng.

## 4. Endpoint / Event trọng tâm

- `POST /access/check`
- `GET /policies/access/{policyId}`
- `GET /health`
- `GET /decisions/{decisionId}`

## 5. Error case / Issue cần nghĩ trước

- Dữ liệu sai định dạng.
- Thiếu thông tin định danh hoặc correlation id.
- Consumer và Provider hiểu khác nhau về trạng thái nghiệp vụ.
- Trùng event/request hoặc retry gây xử lý lặp.
- Timeout hoặc lỗi downstream.

## 6. Câu hỏi gợi ý cho phiên đàm phán

1. Timeout tối đa của /access/check là bao nhiêu?
2. Khi Core lỗi thì Gate fail-open hay fail-closed?
3. Có cần idempotencyKey cho mỗi lượt quẹt không?

## 7. Ghi chú phạm vi Lab 02

Cặp này là REST sync. Hai bên cần viết hoặc chỉnh `openapi.yaml`, chạy Spectral lint và chạy Prism mock server để tạo bằng chứng.
