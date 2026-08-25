"""Generate a synthetic 'soccer field' image and run YOLO on it.
Mục đích: chứng minh YOLO hoạt động đúng trên ảnh có nội dung thật,
không phải 1x1 placeholder."""
from __future__ import annotations

import base64
import io

import requests
from PIL import Image, ImageDraw

# Xanh lá sân + vòng tròn trắng + chấm nhỏ = "bóng"
W, H = 800, 450
img = Image.new("RGB", (W, H), (34, 139, 34))
draw = ImageDraw.Draw(img)
# Sân: vẽ vài vạch trắng
for x in range(0, W, 80):
    draw.line([(x, 0), (x, H)], fill=(255, 255, 255), width=2)
# Bóng tròn trắng ở giữa
draw.ellipse([(W//2 - 20, H//2 - 20), (W//2 + 20, H//2 + 20)], fill=(255, 255, 255))
# "Cầu thủ" màu đỏ
for cx, cy in [(150, 100), (250, 200), (600, 350), (700, 150)]:
    draw.ellipse([(cx - 30, cy - 30), (cx + 30, cy + 30)], fill=(200, 30, 30))
    draw.rectangle([(cx - 10, cy + 30), (cx + 10, cy + 90)], fill=(200, 30, 30))

buf = io.BytesIO()
img.save(buf, format="PNG")
b64 = base64.b64encode(buf.getvalue()).decode()

print(f"Synthetic image: {W}x{H}, {len(buf.getvalue())} bytes PNG")
r = requests.post(
    "http://127.0.0.1:9000/predict",
    json={"image_base64": b64, "confidence_threshold": 0.25},
    timeout=60,
)
print(f"yolo predict: {r.status_code}")
import json
data = r.json()
print(f"mode={data.get('mode')} inference_ms={data.get('inference_time_ms')} dets={len(data.get('detections', []))}")
for d in data.get("detections", []):
    print(f"  - {d['label']:<20} cls={d['class_id']:>2}  conf={d['confidence']:.2f}  bbox={d['bbox']}")
