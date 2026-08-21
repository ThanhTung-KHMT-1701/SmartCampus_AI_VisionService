# User Stories Lab 02

Mỗi cặp đàm phán chọn đúng file tương ứng theo Dependency Map 10 cặp.

| # | Cặp | Cơ chế | File |
|---:|---|---|---|
| 1 | Camera Stream → AI Vision | REST sync | `pair-01-camera-ai-vision.md` |
| 2 | Core Business → AI Vision | REST sync | `pair-02-core-ai-vision.md` |
| 3 | Core Business → Access Gate | REST sync | `pair-03-core-access-gate.md` |
| 4 | Core Business → Notification | Queue async | `pair-04-core-notification-async.md` |
| 5 | IoT Ingestion → Core Business | Queue async | `pair-05-iot-core-async.md` |
| 6 | IoT Ingestion → Analytics | Queue async | `pair-06-iot-analytics-async.md` |
| 7 | Camera Stream → Analytics | Queue async | `pair-07-camera-analytics-async.md` |
| 8 | Core Business → Analytics | Queue async | `pair-08-core-analytics-async.md` |
| 9 | Access Gate → Analytics | Queue async | `pair-09-access-analytics-async.md` |
| 10 | Access Gate → Core Business | REST sync | `pair-10-access-core-policy.md` |

## Cách dùng

- Cặp REST sync: dùng user story để viết `openapi.yaml`.
- Cặp Queue async: dùng user story để ghi nhận event contract sơ bộ và chuyển sang Lab 03 để đặc tả AsyncAPI.

Các user story là khung gợi ý. Giảng viên có thể thay thế bằng user story chi tiết hơn cho từng lớp.
