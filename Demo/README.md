# SmartCampus AI Vision - Streamlit UI

Giao diện web đơn giản để tương tác với AI Vision API.

## Cấu trúc

```
Demo/
├── app.py                    # Main app (sidebar, config)
├── pages/
│   ├── 1_Dashboard.py        # Overview & health check
│   ├── 2_Object_Detection.py # Object detection
│   └── 3_Face_Matching.py    # Face comparison
├── requirements.txt
└── README.md
```

## Cài đặt

```bash
cd Demo
pip install -r requirements.txt
```

## Chạy

```bash
# Copy và sửa .env (hoặc dùng mặc định)
cp .env.example .env

# Chạy app
streamlit run app.py
```

App sẽ mở tại: http://localhost:8501

## Tính năng

| Trang | Mô tả |
|-------|-------|
| Dashboard | Xem health status, model info, recent detections |
| Object Detection | Upload ảnh hoặc nhập URL để detect objects |
| Face Matching | So sánh 2 khuôn mặt |

## Yêu cầu

- Python 3.9+
- AI Vision API đang chạy tại http://localhost:8000
- (Tùy chọn) .env với `AI_VISION_AUTH_TOKEN`
