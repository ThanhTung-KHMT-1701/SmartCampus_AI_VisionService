# Service Boundary – hướng dẫn nhanh

Một boundary tốt trả lời được:

1. Service giải quyết một vấn đề gì?
2. Ai gửi dữ liệu vào (actor/upstream/provider)?
3. Input có schema nào?
4. Service xử lý gì và sở hữu dữ liệu nào?
5. Service **không** làm gì?
6. Output/API/event nào được cung cấp?
7. Consumer/downstream nào bị ảnh hưởng nếu contract thay đổi?

Ví dụ tách đúng:

```text
Camera Stream --frame--> AI Vision --detection--> Core Business --alert--> Notification
```

AI Vision chỉ “phát hiện”; Core Business mới “ra quyết định”.
