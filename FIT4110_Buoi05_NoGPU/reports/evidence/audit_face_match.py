"""Audit face-match endpoint against OpenAPI contract."""
import requests, base64, io
from PIL import Image, ImageDraw

URL = "http://127.0.0.1:8000/vision/face-match"
HDR = {"Authorization": "Bearer local-dev-token-vision"}
TS = "2026-08-25T07:42:40Z"


def make_face_like_b64(label: str = "A") -> str:
    """Tạo ảnh 200x200 CÓ cấu trúc giống khuôn mặt (nền + hình elip trung tâm).

    Đây không phải khuôn mặt thật nhưng đủ để Haar Cascade có thể detect được
    các vùng có gradient giống mặt (mắt, miệng đơn giản hóa).
    """
    img = Image.new("RGB", (200, 200), (220, 200, 180))  # nền da sáng
    draw = ImageDraw.Draw(img)

    # Tóc đậm phía trên
    draw.ellipse([20, 5, 180, 95], fill=(40, 30, 20))

    # Khuôn mặt (elip lớn)
    draw.ellipse([45, 50, 155, 175], fill=(240, 220, 200))

    # Mắt trái + phải
    draw.ellipse([70, 90, 90, 105], fill=(255, 255, 255))
    draw.ellipse([75, 92, 85, 102], fill=(40, 40, 80))  # pupil
    draw.ellipse([110, 90, 130, 105], fill=(255, 255, 255))
    draw.ellipse([115, 92, 125, 102], fill=(40, 40, 80))

    # Mũi
    draw.polygon([(95, 110), (105, 110), (100, 135)], fill=(210, 180, 160))

    # Miệng
    draw.ellipse([82, 145, 118, 160], fill=(180, 60, 60))

    # Lưu thành JPEG base64
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def make_no_face_b64() -> str:
    """Ảnh phong cảnh đơn giản — KHÔNG có khuôn mặt."""
    img = Image.new("RGB", (200, 200), (30, 100, 200))  # bầu trời xanh
    draw = ImageDraw.Draw(img)
    # Núi xanh
    draw.polygon([(0, 200), (60, 130), (110, 170), (160, 120), (200, 200)], fill=(40, 120, 60))
    # Mặt trời
    draw.ellipse([150, 20, 180, 50], fill=(255, 220, 50))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


FACE_A = make_face_like_b64("A")
FACE_B = make_face_like_b64("B")  # 2 ảnh "mặt" KHÁC nhau (variation nhỏ)
NO_FACE = make_no_face_b64()

cases = [
    ("Case A: ảnh MẶT_A vs ảnh KHÔNG-MẶT (expect ERROR)",
     {"image_base64": FACE_A, "reference_image_base64": NO_FACE,
      "threshold": 0.75, "timestamp": TS, "trace_id": "trace-test-A"}),
    ("Case B: ảnh MẶT vs ảnh MẶT GIỐNG NHAU (expect MATCHED, cùng 1 ảnh)",
     {"image_base64": FACE_A, "reference_image_base64": FACE_A,
      "threshold": 0.70, "timestamp": TS, "trace_id": "trace-test-B"}),
    ("Case C: 2 ảnh MẶT HƠI KHÁC nhau (expect NOT_MATCHED hoặc LOW_CONFIDENCE)",
     {"image_base64": FACE_A, "reference_image_base64": FACE_B,
      "threshold": 0.85, "timestamp": TS, "trace_id": "trace-test-C"}),
    ("Case D: URL không phải URI (abc) — sai schema",
     {"image_url": "abc", "reference_image_url": "abc", "threshold": 0.75,
      "timestamp": TS, "trace_id": "trace-test-D"}),
    ("Case E: URL thật nhưng ảnh không có mặt (xe)",
     {"image_url": "http://httpbin.org/image/jpeg",
      "reference_image_url": "http://httpbin.org/image/jpeg",
      "threshold": 0.70, "timestamp": TS, "trace_id": "trace-test-E"}),
    ("Case F: ảnh MẶT_A vs ảnh MẶT_A GIỐNG NHAU (expect MATCHED, same hash)",
     {"image_base64": FACE_A, "reference_image_base64": FACE_A,
      "threshold": 0.50, "timestamp": TS, "trace_id": "trace-test-F"}),
]

print("=" * 70)
for name, body in cases:
    print(name)
    r = requests.post(URL, headers=HDR, json=body, timeout=30)
    print(f"  HTTP {r.status_code}")
    if r.status_code == 200:
        b = r.json()
        print(f"  matched={b.get('matched')}  confidence={b.get('confidence')}  "
              f"status={b.get('status')}  proc_ms={b.get('processing_time_ms')}")
        print(f"  message={b.get('message')!r}")
    else:
        try:
            errs = r.json().get("errors", [])
            for e in errs[:2]:
                print(f"  - {e.get('field')}: {e.get('code')}: {e.get('message')}")
        except Exception:
            print(f"  body: {r.text[:150]}")
    print()
