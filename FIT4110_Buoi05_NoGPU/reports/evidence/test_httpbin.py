import requests, json, time

t0 = time.perf_counter()
r = requests.post(
    "http://127.0.0.1:8000/vision/detect",
    headers={"Authorization": "Bearer local-dev-token-vision"},
    json={
        "camera_id": "cam-gate-01",
        "image_url": "https://httpbin.org/image/jpeg",
        "timestamp": "2026-08-22T07:30:00Z",
        "confidence_threshold": 0.25,
    },
    timeout=30,
)
elapsed = int((time.time() - t0) * 1000)
print(f"HTTP {r.status_code}  elapsed={elapsed}ms")
if r.status_code == 200:
    b = r.json()
    print(f"detections={len(b.get('detections', []))}")
    for d in b.get("detections", []):
        print(f"  {d['label']} {d['confidence']}")
else:
    print(r.text[:300])
