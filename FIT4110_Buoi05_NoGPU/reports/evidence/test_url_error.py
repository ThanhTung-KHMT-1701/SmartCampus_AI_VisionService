"""Test face-match trả Problem+JSON 400 đúng contract khi URL fetch fail."""
import requests

URL = "http://127.0.0.1:8000/vision/face-match"
HDR = {"Authorization": "Bearer local-dev-token-vision"}
TS = "2026-08-25T08:00:00Z"


def post(name, body):
    print(f"\n--- {name} ---")
    r = requests.post(URL, headers=HDR, json=body, timeout=20)
    print(f"HTTP {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type')}")
    try:
        import json
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text[:200])
    return r


# Case 1: URL 404 — không trỏ đến ảnh thật
post("URL 404 (Not Found)",
     {"image_url": "http://httpbin.org/status/404",
      "reference_image_url": "http://httpbin.org/image/jpeg",
      "threshold": 0.75, "timestamp": TS, "trace_id": "url-404"})

# Case 2: URL domain không tồn tại
post("URL domain không tồn tại (DNS fail)",
     {"image_url": "http://nonexistent-domain-cabcab-xyz-12345.invalid/x.jpg",
      "reference_image_url": "http://httpbin.org/image/jpeg",
      "threshold": 0.75, "timestamp": TS, "trace_id": "url-dns"})

# Case 3: Reference URL 404, query OK
post("Reference URL 404",
     {"image_url": "http://httpbin.org/image/jpeg",
      "reference_image_url": "http://httpbin.org/status/404",
      "threshold": 0.75, "timestamp": TS, "trace_id": "ref-404"})

# Case 4: URL 500
post("URL 500 (server error)",
     {"image_url": "http://httpbin.org/status/500",
      "reference_image_url": "http://httpbin.org/image/jpeg",
      "threshold": 0.75, "timestamp": TS, "trace_id": "url-500"})