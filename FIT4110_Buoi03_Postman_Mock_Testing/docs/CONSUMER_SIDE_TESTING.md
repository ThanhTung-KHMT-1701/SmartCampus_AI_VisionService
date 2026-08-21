# CONSUMER-SIDE TESTING — Kiểm thử từ phía nhóm gọi API

## 1. Vì sao cần consumer-side test?

Trong hệ thống Smart Campus, không nhóm nào làm việc độc lập hoàn toàn.

Ví dụ:

```text
Camera Stream → AI Vision → Core Business → Notification
IoT Ingestion → Core Business
IoT Ingestion → Analytics
Access Gate → Core Business
```

Nếu phải chờ provider code xong mới làm tiếp, toàn bộ lớp sẽ bị nghẽn.  
Vì vậy, consumer cần gọi được **mock API** của provider.

---

## 2. Quy trình handshake giữa consumer và provider

### Bước 1 — Provider công bố contract

Provider đưa cho consumer:

```text
openapi.yaml
mock_base_url
auth rule
example request
example response
```

### Bước 2 — Consumer tạo smoke test

Consumer tạo ít nhất 1 request gọi mock provider.

Ví dụ Camera gọi AI Vision mock:

```http
POST {{aiVisionMockUrl}}/detect
Authorization: Bearer {{authToken}}
Content-Type: application/json

{
  "camera_id": "CAM01",
  "image_url": "https://example.com/frame.jpg"
}
```

Expected:

```json
{
  "detection_id": "DET001",
  "label": "person",
  "confidence": 0.91,
  "risk_level": "medium"
}
```

### Bước 3 — Ghi biên bản

Dùng template:

```text
templates/consumer-provider-handshake.md
```

---

## 3. Tiêu chí pass

Consumer-side smoke test đạt khi:

- Gọi đúng endpoint của provider.
- Request body đúng schema.
- Đọc được field cần dùng trong response.
- Xử lý được ít nhất 1 lỗi 4xx hoặc 5xx.
- Có ảnh chụp màn hình hoặc Newman report.
