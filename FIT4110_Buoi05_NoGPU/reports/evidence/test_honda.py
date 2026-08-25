"""Test YOLO trên ảnh Honda AirBlade thật."""
import base64, requests, json

img_bytes = open("reports/evidence/honda.jpg", "rb").read()
print(f"Image: {len(img_bytes)} bytes, first bytes: {img_bytes[:20].hex()}")
b64 = base64.b64encode(img_bytes).decode()

r = requests.post(
    "http://127.0.0.1:9000/predict",
    json={"image_base64": b64, "confidence_threshold": 0.25},
    timeout=60,
)
print(f"yolo predict: {r.status_code}")
data = r.json()
print(f"mode={data.get('mode')} inference_ms={data.get('inference_time_ms')} dets={len(data.get('detections', []))}")
for d in data.get("detections", []):
    print(f"  - {d['label']:<20} cls={d['class_id']:>2}  conf={d['confidence']:.2f}  bbox={d['bbox']}")

# Lưu ảnh kèm bbox overlay
try:
    from PIL import Image, ImageDraw
    img = Image.open("reports/evidence/honda.jpg").convert("RGB")
    dr = ImageDraw.Draw(img)
    for d in data.get("detections", []):
        b = d["bbox"]
        dr.rectangle([(b["x"], b["y"]), (b["x"]+b["width"], b["y"]+b["height"])], outline=(255,0,0), width=3)
        dr.text((b["x"], max(0, b["y"]-15)), f"{d['label']} {d['confidence']:.2f}", fill=(255,0,0))
    img.save("reports/evidence/honda_yolo.png")
    print("Saved overlay: reports/evidence/honda_yolo.png")
except Exception as e:
    print(f"overlay err: {e}")
