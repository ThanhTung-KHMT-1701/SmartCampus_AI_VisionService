# User Story — Core Business → AI Vision

## 1. Cơ chế

**REST sync**

## 2. Bối cảnh

Core Business lấy hoặc yêu cầu kết quả phân tích ảnh/face-match từ AI Vision để ra quyết định nghiệp vụ.

## 3. Nhu cầu của Consumer

Consumer cần thông tin detection/face-match có confidence, modelVersion, timestamp và traceId để audit.

## 4. Endpoint / Event trọng tâm

- `POST /vision/face-match`
- `GET /vision/detections/{detectionId}`
- `GET /vision/results/recent`
- `GET /health`

## 5. Error case / Issue cần nghĩ trước

- Dữ liệu sai định dạng.
- Thiếu thông tin định danh hoặc correlation id.
- Consumer và Provider hiểu khác nhau về trạng thái nghiệp vụ.
- Trùng event/request hoặc retry gây xử lý lặp.
- Timeout hoặc lỗi downstream.

## 6. Câu hỏi gợi ý cho phiên đàm phán

1. Core gửi faceEmbedding hay imageRef?
2. Ngưỡng confidence bao nhiêu thì coi là match?
3. Khi model không chắc chắn thì trả 200 với trạng thái low_confidence hay 422?

## 7. Ghi chú phạm vi Lab 02

Cặp này là REST sync. Hai bên cần viết hoặc chỉnh `openapi.yaml`, chạy Spectral lint và chạy Prism mock server để tạo bằng chứng.
