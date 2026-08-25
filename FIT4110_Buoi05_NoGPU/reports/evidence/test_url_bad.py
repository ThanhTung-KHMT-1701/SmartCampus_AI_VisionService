"""Test bad/good URL để tìm nguyên nhân."""
import requests, json

CASES = [
    ("URL ĐÚNG (có .png)",
     "https://png.pngtree.com/png-vector/20250430/ourmid/pngtree-sleek-white-car-modern-sedan-png-image_16155268.png"),
    ("URL SAI (xóa số 8)",
     "https://png.pngtree.com/png-vector/20250430/ourmid/pngtree-sleek-white-car-modern-sedan-png-image_1615526.png"),
    ("URL gốc trong test (có ?)",
     "https://png.pngtree.com/png-vector/20250430/ourmid/pngtree-sleek-white-car-modern-sedan-png-image_1615526.png"),
]

for name, url in CASES:
    print(f"\n=== {name} ===")
    print(f"   URL: {url}")
    r = requests.post(
        "http://127.0.0.1:8000/vision/detect",
        headers={"Authorization": "Bearer local-dev-token-vision"},
        json={
            "camera_id": "cam-gate-01",
            "image_url": url,
            "timestamp": "2026-08-22T07:30:00Z",
            "confidence_threshold": 0.5,
        },
        timeout=60,
    )
    print(f"   HTTP: {r.status_code}")
    body = r.json()
    print(f"   detections: {len(body.get('detections', []))}")
    for d in body.get("detections", []):
        print(f"     - {d['label']:<12} conf={d['confidence']}")