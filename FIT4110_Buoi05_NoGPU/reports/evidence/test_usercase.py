"""Verify the exact user case: typo URL (xóa số 8) must NOT return 200 detections."""
import requests

GOOD = "https://png.pngtree.com/png-vector/20250430/ourmid/pngtree-sleek-white-car-modern-sedan-png-image_16155268.png"
BAD = "https://png.pngtree.com/png-vector/20250430/ourmid/pngtree-sleek-white-car-modern-sedan-png-image_1615526.png"

print("=== Case 1: URL sai (xóa số 8) ===")
r = requests.post(
    "http://127.0.0.1:8000/vision/detect",
    headers={"Authorization": "Bearer local-dev-token-vision"},
    json={"camera_id": "cam-gate-01", "image_url": BAD, "timestamp": "2026-08-22T07:30:00Z"},
    timeout=30,
)
print(f"HTTP: {r.status_code}")
print(f"Body: {r.text[:300]}")

print()
print("=== Case 2: URL ĐÚNG ===")
r = requests.post(
    "http://127.0.0.1:8000/vision/detect",
    headers={"Authorization": "Bearer local-dev-token-vision"},
    json={"camera_id": "cam-gate-01", "image_url": GOOD, "timestamp": "2026-08-22T07:30:00Z"},
    timeout=30,
)
print(f"HTTP: {r.status_code}")
if r.status_code == 200:
    body = r.json()
    print(f"detections: {len(body.get('detections', []))}")
    for d in body.get("detections", [])[:3]:
        print(f"  {d['label']} {d['confidence']}")
else:
    print(f"Body: {r.text[:300]}")
