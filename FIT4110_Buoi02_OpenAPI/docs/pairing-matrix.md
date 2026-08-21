# Dependency Map và Pairing Matrix — Smart Campus Operations Platform

Tài liệu này dùng để xác định các cặp phụ thuộc giữa service trong Smart Campus. 
> Lưu ý: Lab 02 tập trung vào **OpenAPI 3.1 cho REST sync**. Các cặp Queue async vẫn được đưa vào ma trận để sinh viên thấy dependency đầy đủ, nhưng phần đặc tả chi tiết topic/message schema sẽ được chuyển sâu sang Lab 03 bằng AsyncAPI hoặc event contract riêng.

| # | Consumer | Provider | Mục đích | Cơ chế | Phạm vi Lab 02 | User story |
|---:|---|---|---|---|---|---|
| 1 | Camera Stream (A2/B2) | AI Vision (A4/B4) | Gửi frame khi phát hiện motion | REST sync | Viết OpenAPI | `user-stories/pair-01-camera-ai-vision.md` |
| 2 | Core Business (A6/B6) | AI Vision (A4/B4) | Lấy kết quả phân tích ảnh / detect | REST sync | Viết OpenAPI | `user-stories/pair-02-core-ai-vision.md` |
| 3 | Core Business (A6/B6) | Access Gate (A3/B3) | Nhận log quẹt thẻ / kiểm tra trạng thái cổng | REST sync | Viết OpenAPI | `user-stories/pair-03-core-access-gate.md` |
| 4 | Core Business (A6/B6) | Notification (A7/B7) | Trigger gửi alert đa kênh | Queue async | Ghi nhận event contract, để Lab 03 đặc tả AsyncAPI | `user-stories/pair-04-core-notification-async.md` |
| 5 | IoT Ingestion (A1/B1) | Core Business (A6/B6) | Publish event sensor mới | Queue async | Ghi nhận event contract, để Lab 03 đặc tả AsyncAPI | `user-stories/pair-05-iot-core-async.md` |
| 6 | IoT Ingestion (A1/B1) | Analytics (A5/B5) | Feed telemetry cho aggregate | Queue async | Ghi nhận event contract, để Lab 03 đặc tả AsyncAPI | `user-stories/pair-06-iot-analytics-async.md` |
| 7 | Camera Stream (A2/B2) | Analytics (A5/B5) | Feed event camera cho aggregate | Queue async | Ghi nhận event contract, để Lab 03 đặc tả AsyncAPI | `user-stories/pair-07-camera-analytics-async.md` |
| 8 | Core Business (A6/B6) | Analytics (A5/B5) | Feed event alert / policy cho KPI | Queue async | Ghi nhận event contract, để Lab 03 đặc tả AsyncAPI | `user-stories/pair-08-core-analytics-async.md` |
| 9 | Access Gate (A3/B3) | Analytics (A5/B5) | Feed log ra/vào cho thống kê | Queue async | Ghi nhận event contract, để Lab 03 đặc tả AsyncAPI | `user-stories/pair-09-access-analytics-async.md` |
| 10 | Access Gate (A3/B3) | Core Business (A6/B6) | Kiểm tra policy ra/vào realtime | REST sync | Viết OpenAPI | `user-stories/pair-10-access-core-policy.md` |

## Cách dùng trong Lab 02

### Nhóm thuộc cặp REST sync

Các cặp số **1, 2, 3, 10** phải hoàn thiện đầy đủ:

```text
openapi.yaml
negotiation-log.md
docs/analysis-provider.md
docs/analysis-consumer.md
evidence/buoi-02/spectral-report.txt
evidence/buoi-02/mock-screenshots/
```

### Nhóm thuộc cặp Queue async

Các cặp số **4, 5, 6, 7, 8, 9** chưa cần viết AsyncAPI trong Lab 02. Tuy nhiên, hai bên vẫn cần đàm phán tối thiểu các điểm sau và ghi vào `negotiation-log.md`:

- tên event/topic;
- producer và consumer;
- payload tối thiểu;
- idempotency key hoặc event id;
- timestamp và correlation id;
- retry/dead-letter assumption;
- vấn đề cần chuyển sang Lab 03.

Nếu giảng viên muốn chấm riêng Queue async ngay ở Lab 02, có thể dùng file `docs/event-contract-template.md` làm mẫu ghi nhận hợp đồng sự kiện sơ bộ.

## Gợi ý chia tải cho nhóm Core Business

Core Business xuất hiện ở nhiều dependency nên cần phân công nội bộ rõ ràng.

| Thành viên | Dependency phụ trách | Ghi chú |
|---|---|---|
| Thành viên 1 | Core ↔ AI Vision | Nhận/lấy kết quả phân tích ảnh |
| Thành viên 2 | Core ↔ Access Gate | Log cổng và policy realtime |
| Thành viên 3 | Core → Notification | Alert event / gửi thông báo |
| Thành viên 4 | IoT → Core | Sensor event |
| Thành viên 5 | Core → Analytics | Alert/policy KPI |

Mỗi thành viên nên phụ trách 1–2 dependency để tránh dồn toàn bộ phiên đàm phán vào một người.
