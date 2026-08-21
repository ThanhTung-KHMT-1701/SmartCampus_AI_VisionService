# Event Contract sơ bộ — dùng cho dependency Queue async

> File này chỉ dùng cho các cặp Queue async ở Lab 02 để ghi nhận thỏa thuận ban đầu. Đặc tả chi tiết bằng AsyncAPI sẽ chuyển sang Lab 03.

## 1. Thông tin dependency

- Dependency số:
- Producer:
- Consumer:
- Cơ chế: Queue async
- Event/topic dự kiến:
- Người ghi:
- Ngày:

## 2. Mục đích nghiệp vụ

Mô tả ngắn event này sinh ra khi nào và consumer dùng để làm gì.

## 3. Event name / topic

| Mục | Giá trị |
|---|---|
| Event name | `<domain.event.action>` |
| Topic/queue | `<topic-name>` |
| Producer | `<service>` |
| Consumer | `<service>` |

## 4. Payload tối thiểu

```json
{
  "eventId": "uuid",
  "eventType": "domain.event.created",
  "occurredAt": "2026-05-10T08:30:00Z",
  "correlationId": "uuid",
  "source": "service-name",
  "data": {}
}
```

## 5. Ràng buộc cần thống nhất

| Vấn đề | Quyết định tạm thời |
|---|---|
| Event id có bắt buộc không? | Có |
| Có cần correlationId không? | Có |
| Có cho phép gửi trùng event không? | Có thể, consumer phải idempotent |
| Retry khi lỗi | Ghi rõ ở Lab 03 |
| Dead-letter queue | Ghi rõ ở Lab 03 |

## 6. Issue chuyển sang Lab 03

1. ...
2. ...
3. ...
