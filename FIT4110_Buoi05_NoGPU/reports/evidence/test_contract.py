"""Verify URL bad/no-uri fail-fast per OpenAPI contract."""
import requests

URL = "http://127.0.0.1:8000/vision/detect"
HDR = {"Authorization": "Bearer local-dev-token-vision"}
TS = "2026-08-22T07:30:00Z"

cases = [
    ("URL không phải URI hợp lệ (chỉ chữ)",
     {"camera_id": "cam-1", "image_url": "abc", "timestamp": TS}),
    ("URL scheme không hợp lệ (ftp)",
     {"camera_id": "cam-1", "image_url": "ftp://x/y.jpg", "timestamp": TS}),
    ("URL không tồn tại (404)",
     {"camera_id": "cam-1", "image_url": "https://httpbin.org/status/404", "timestamp": TS}),
    ("URL từ chối (403)",
     {"camera_id": "cam-1", "image_url": "https://httpbin.org/status/403", "timestamp": TS}),
    ("URL thật 200 (httpbin image)",
     {"camera_id": "cam-1", "image_url": "https://httpbin.org/image/jpeg", "timestamp": TS,
      "confidence_threshold": 0.25}),
]

for name, body in cases:
    r = requests.post(URL, headers=HDR, json=body, timeout=30)
    snippet = (r.text[:160] + "...") if len(r.text) > 160 else r.text
    print(f"[{r.status_code}] {name}")
    print(f"      {snippet}")
    print()
