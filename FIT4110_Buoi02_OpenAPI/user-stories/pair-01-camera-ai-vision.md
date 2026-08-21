# User Story — Camera Stream → AI Vision

## 1. Cơ chế

**REST sync**

## 2. Bối cảnh

Camera Stream gửi frame hoặc image metadata khi phát hiện motion để AI Vision chạy detect.

## 3. Nhu cầu của Consumer

Consumer cần response nhanh gồm detectionId, objects, confidence và riskLevel để chuyển tiếp cho Core Business khi có bất thường.

## 4. Endpoint / Event trọng tâm

- `POST /vision/detect`
- `GET /vision/detections/{detectionId}`
- `GET /vision/models/info`
- `GET /health`

## 5. Error case / Issue cần nghĩ trước

- Dữ liệu sai định dạng.
- Thiếu thông tin định danh hoặc correlation id.
- Consumer và Provider hiểu khác nhau về trạng thái nghiệp vụ.
- Trùng event/request hoặc retry gây xử lý lặp.
- Timeout hoặc lỗi downstream.

## 6. Câu hỏi gợi ý cho phiên đàm phán

1. Ảnh gửi dạng multipart hay URL?
2. Giới hạn kích thước frame là bao nhiêu?
3. AI Vision trả kết quả đồng bộ hay trả detectionId để polling?

## 7. Ghi chú phạm vi Lab 02

Cặp này là REST sync. Hai bên cần viết hoặc chỉnh `openapi.yaml`, chạy Spectral lint và chạy Prism mock server để tạo bằng chứng.
