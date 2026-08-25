"""Test với fix fail-fast: URL sai phải trả lỗi, không trả detection giả."""
import requests

BAD_URL = "https://png.pngtree.com/png-vector/20250430/ourmid/pngtree-sleek-white-car-modern-sedan-png-image_1615526.png"
GOOD_URL = "https://png.pngtree.com/png-vector/20250430/ourmid/pngtree-sleek-white-car-modern-sedan-png-image_16155268.png"

print("=== Case 1: URL BAD (xóa số 8) — phải trả lỗi 4xx/5xx ===")
r1 = requests.post(
    "http://127.0.0.1:8000/vision/detect",
    headers={"Authorization": "Bearer local-dev-token-vision"},
    json={
        "camera_id": "cam-gate-01",
        "image_url": BAD_URL,
        "timestamp": "2026-08-22T07:30:00Z",
        "confidence_threshold": 0.5,
    },
    timeout=30,
)
print(f"HTTP: {r1.status_code}")
print(f"Body: {r1.text[:400]}")

print()
print("=== Case 2: URL GOOD — phải trả car thật ===")
r2 = requests.post(
    "http://127.0.0.1:8000/vision/detect",
    headers={"Authorization": "Bearer local-dev-token-vision"},
    json={
        "camera_id": "cam-gate-01",
        "image_url": GOOD_URL,
        "timestamp": "2026-08-22T07:30:00Z",
        "confidence_threshold": 0.5,
    },
    timeout=30,
)
print(f"HTTP: {r2.status_code}")
b2 = r2.json()
print(f"detections: {len(b2.get('detections', []))}")
for d in b2.get("detections", []):
    print(f"  - {d['label']:<12} conf={d['confidence']}")

print()
print("=== Case 3: URL BAD gọi thẳng ai-yolo ===")
r3 = requests.post(
    "http://127.0.0.1:9000/predict",
    json={"image_url": BAD_URL, "confidence_threshold": 0.5},
    timeout=30,
)
print(f"HTTP: {r3.status_code}")
print(f"Body: {r3.text[:400]}")
