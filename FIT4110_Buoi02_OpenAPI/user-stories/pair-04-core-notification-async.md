# User Story — Core Business → Notification

## 1. Cơ chế

**Queue async**

## 2. Bối cảnh

Core Business phát event alert để Notification gửi thông báo đa kênh như Telegram, email hoặc app message.

## 3. Nhu cầu của Consumer

Ở Lab 02 chỉ thống nhất event name, payload tối thiểu và retry assumption; chi tiết AsyncAPI để Lab 03.

## 4. Endpoint / Event trọng tâm

- `Event alert.created`
- `Event alert.escalated`
- `Event alert.resolved`

## 5. Error case / Issue cần nghĩ trước

- Dữ liệu sai định dạng.
- Thiếu thông tin định danh hoặc correlation id.
- Consumer và Provider hiểu khác nhau về trạng thái nghiệp vụ.
- Trùng event/request hoặc retry gây xử lý lặp.
- Timeout hoặc lỗi downstream.

## 6. Câu hỏi gợi ý cho phiên đàm phán

1. Event alert.created cần field severity không?
2. Notification có cần nhận danh sách channel hay tự định tuyến?
3. Nếu gửi thất bại thì retry do queue hay Notification tự xử lý?

## 7. Ghi chú phạm vi Lab 02

Cặp này là Queue async. Trong Lab 02, hai bên chưa cần viết AsyncAPI đầy đủ. Tuy nhiên, cần ghi rõ thỏa thuận sơ bộ trong `negotiation-log.md` hoặc dùng `docs/event-contract-template.md` nếu giảng viên yêu cầu.
