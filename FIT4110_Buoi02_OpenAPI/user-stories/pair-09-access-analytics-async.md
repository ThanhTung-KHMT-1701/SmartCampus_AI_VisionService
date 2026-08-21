# User Story — Access Gate → Analytics

## 1. Cơ chế

**Queue async**

## 2. Bối cảnh

Access Gate feed log ra/vào cho Analytics để thống kê lưu lượng, giờ cao điểm và tỷ lệ deny.

## 3. Nhu cầu của Consumer

Ở Lab 02 chỉ thống nhất payload log và idempotency.

## 4. Endpoint / Event trọng tâm

- `Event access.log.created`
- `Event access.denied`

## 5. Error case / Issue cần nghĩ trước

- Dữ liệu sai định dạng.
- Thiếu thông tin định danh hoặc correlation id.
- Consumer và Provider hiểu khác nhau về trạng thái nghiệp vụ.
- Trùng event/request hoặc retry gây xử lý lặp.
- Timeout hoặc lỗi downstream.

## 6. Câu hỏi gợi ý cho phiên đàm phán

1. direction dùng IN/OUT hay ENTER/EXIT?
2. Có cần hash cardId để bảo vệ dữ liệu cá nhân không?
3. Một lần quẹt lỗi có tạo log không?

## 7. Ghi chú phạm vi Lab 02

Cặp này là Queue async. Trong Lab 02, hai bên chưa cần viết AsyncAPI đầy đủ. Tuy nhiên, cần ghi rõ thỏa thuận sơ bộ trong `negotiation-log.md` hoặc dùng `docs/event-contract-template.md` nếu giảng viên yêu cầu.
