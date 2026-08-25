"""Test face-match crash protection + exact contract message."""
import requests, base64, io
from PIL import Image

URL = "http://127.0.0.1:8001/vision/face-match"
HDR = {"Authorization": "Bearer local-dev-token-vision"}
TS = "2026-08-25T08:00:00Z"


def fake_img_b64(label="x"):
    img = Image.new("RGB", (40, 40), (200, 100, 50))
    buf = io.BytesIO(); img.save(buf, "JPEG"); return base64.b64encode(buf.getvalue()).decode()


# 1) Ảnh hỏng: base64 nhưng PIL không đọc được (random bytes)
bad_b64 = base64.b64encode(b"this is not a valid image data at all!!!").decode()

# 2) Ảnh nhỏ không có mặt
small_b64 = fake_img_b64("small")

# 3) Ảnh mặt thật (200x200 vẽ elip)
def make_face():
    img = Image.new("RGB", (200, 200), (220, 200, 180))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.ellipse([20, 5, 180, 95], fill=(40, 30, 20))
    d.ellipse([45, 50, 155, 175], fill=(240, 220, 200))
    d.ellipse([70, 90, 90, 105], fill=(255, 255, 255))
    d.ellipse([75, 92, 85, 102], fill=(40, 40, 80))
    d.ellipse([110, 90, 130, 105], fill=(255, 255, 255))
    d.ellipse([115, 92, 125, 102], fill=(40, 40, 80))
    d.polygon([(95, 110), (105, 110), (100, 135)], fill=(210, 180, 160))
    d.ellipse([82, 145, 118, 160], fill=(180, 60, 60))
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

FACE = make_face()

cases = [
    ("1. Ảnh hỏng (random bytes, PIL error) — expect 200 ERROR, NO CRASH",
     {"image_base64": bad_b64, "reference_image_base64": bad_b64,
      "threshold": 0.75, "timestamp": TS, "trace_id": "crash-test-1"}),
    ("2. Ảnh nhỏ không có mặt — expect 200 ERROR",
     {"image_base64": small_b64, "reference_image_base64": small_b64,
      "threshold": 0.75, "timestamp": TS, "trace_id": "crash-test-2"}),
    ("3. Ảnh mặt vs ảnh không mặt — expect 200 ERROR",
     {"image_base64": FACE, "reference_image_base64": small_b64,
      "threshold": 0.75, "timestamp": TS, "trace_id": "crash-test-3"}),
    ("4. Ảnh mặt vs ảnh mặt (cùng ảnh) — expect 200 MATCHED",
     {"image_base64": FACE, "reference_image_base64": FACE,
      "threshold": 0.70, "timestamp": TS, "trace_id": "crash-test-4"}),
]

all_ok = True
print("=" * 70)
for name, body in cases:
    print(name)
    try:
        r = requests.post(URL, headers=HDR, json=body, timeout=20)
        b = r.json()
        print(f"  HTTP {r.status_code}  matched={b.get('matched')}  "
              f"conf={b.get('confidence')}  status={b.get('status')}")
        print(f"  message={b.get('message')!r}")
        if r.status_code != 200:
            print(f"  FAIL: expected HTTP 200")
            all_ok = False
        if b.get('status') == 'ERROR' and 'Không phát hiện khuôn mặt' not in b.get('message', ''):
            print(f"  FAIL: message không đúng contract")
            all_ok = False
    except Exception as e:
        print(f"  CRASH: {e}")
        all_ok = False
    print()

print("=" * 70)
print("RESULT:", "ALL PASS" if all_ok else "SOME FAILED")
