"""Test detect qua ai-vision (có auth + image_url) với ảnh Honda."""
import requests, json

r = requests.post(
    "http://127.0.0.1:8000/vision/detect",
    headers={"Authorization": "Bearer local-dev-token-vision"},
    json={
        "camera_id": "cam-test",
        "image_url": "https://denledxe.com/uploads/page/2020_12/Honda-AirBlade-150-2021.jpg",
        "timestamp": "2026-08-25T07:40:00Z",
        "confidence_threshold": 0.25,
    },
    timeout=60,
)
print(f"vision/detect: {r.status_code}")
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
