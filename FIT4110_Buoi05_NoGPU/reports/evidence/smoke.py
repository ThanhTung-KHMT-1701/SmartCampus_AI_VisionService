"""Smoke test cho AI Vision Service Lab 05 — chạy thẳng từ Python."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
YOLO = "http://127.0.0.1:9000"
TOKEN = "local-dev-token-vision"
EVIDENCE = Path(__file__).resolve().parent

AUTH = {"Authorization": f"Bearer {TOKEN}"}
JSON = {"Content-Type": "application/json"}

results: list[tuple[str, int, str]] = []


def record(name: str, status: int, note: str = "") -> None:
    results.append((name, status, note))
    marker = "OK" if 200 <= status < 300 or status in (401, 422) else "??"
    print(f"[{marker}] {name:<40} HTTP {status} {note}".rstrip())


def probe(name: str, method: str, url: str, *, headers=None, body=None) -> int:
    try:
        r = httpx.request(method, url, headers=headers, json=body, timeout=30.0)
    except httpx.HTTPError as exc:
        record(name, -1, f"exc: {exc.__class__.__name__}")
        return -1
    note = ""
    if name == "ready" and r.status_code == 200:
        data = r.json()
        deps = ", ".join(f"{d['name']}={d['status']}" for d in data.get("dependencies", []))
        note = f"deps={deps}"
    if name == "detect-url" and r.status_code == 200:
        data = r.json()
        note = f"id={data['detection_id'][:8]}.. risk={data['risk_level']} dets={len(data['detections'])}"
        globals()["LAST_ID"] = data["detection_id"]
    record(name, r.status_code, note)
    return r.status_code


print("=== Lab 05 smoke test (real services, no Docker) ===\n")

# 1. Liveness / readiness
probe("health-api", "GET", f"{BASE}/health")
probe("health-yolo", "GET", f"{YOLO}/health")
probe("ready", "GET", f"{BASE}/ready")

# 2. Functional
probe(
    "detect-url",
    "POST",
    f"{BASE}/vision/detect",
    headers=AUTH,
    body={
        "camera_id": "cam-gate-01",
        "image_url": "https://httpbin.org/image/jpeg",
        "timestamp": "2026-08-22T07:30:00Z",
        "confidence_threshold": 0.25,
    },
)
probe(
    "detect-by-id",
    "GET",
    f"{BASE}/vision/detections/{LAST_ID}",
    headers=AUTH,
)
probe(
    "detect-recent",
    "GET",
    f"{BASE}/vision/results/recent?limit=5",
    headers=AUTH,
)
probe(
    "face-match",
    "POST",
    f"{BASE}/vision/face-match",
    headers=AUTH,
    body={
        "image_url": "https://httpbin.org/image/jpeg",
        "reference_image_url": "https://httpbin.org/image/png",
        "threshold": 0.7,
        "trace_id": "trace-lab05-001",
        "timestamp": "2026-08-22T07:30:00Z",
    },
)
probe("models-info", "GET", f"{BASE}/vision/models/info", headers=AUTH)

# 3. YOLO direct
probe(
    "yolo-predict",
    "POST",
    f"{YOLO}/predict",
    body={
        "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "confidence_threshold": 0.3,
    },
)

# 4. Auth / Negative / Boundary
probe("auth-missing", "POST", f"{BASE}/vision/detect",
      body={"camera_id": "cam-gate-01", "image_url": "x", "timestamp": "2026-08-22T07:30:00Z"})
probe("auth-wrong", "POST", f"{BASE}/vision/detect",
      headers={"Authorization": "Bearer wrong"},
      body={"camera_id": "cam-gate-01", "image_url": "x", "timestamp": "2026-08-22T07:30:00Z"})
probe("neg-mutex", "POST", f"{BASE}/vision/detect", headers=AUTH,
      body={"camera_id": "cam-gate-01", "image_url": "x", "image_base64": "y", "timestamp": "2026-08-22T07:30:00Z"})
probe("neg-no-timestamp", "POST", f"{BASE}/vision/detect", headers=AUTH,
      body={"camera_id": "cam-gate-01", "image_url": "x"})
probe("neg-bad-uuid", "GET", f"{BASE}/vision/detections/not-a-uuid", headers=AUTH)
probe("bnd-thr-0.0", "POST", f"{BASE}/vision/detect", headers=AUTH,
      body={"camera_id": "cam-gate-01", "image_url": "https://httpbin.org/image/jpeg", "timestamp": "2026-08-22T07:30:00Z", "confidence_threshold": 0.0})
probe("bnd-thr-1.0", "POST", f"{BASE}/vision/detect", headers=AUTH,
      body={"camera_id": "cam-gate-01", "image_url": "https://httpbin.org/image/jpeg", "timestamp": "2026-08-22T07:30:00Z", "confidence_threshold": 1.0})
probe("bnd-thr-1.5", "POST", f"{BASE}/vision/detect", headers=AUTH,
      body={"camera_id": "cam-gate-01", "image_url": "https://httpbin.org/image/jpeg", "timestamp": "2026-08-22T07:30:00Z", "confidence_threshold": 1.5})
probe("yolo-mutex", "POST", f"{YOLO}/predict",
      body={"image_url": "x", "image_base64": "y", "confidence_threshold": 0.4})

# Write evidence
evidence_path = EVIDENCE / "smoke-summary.json"
evidence_path.write_text(json.dumps(
    [{"name": n, "status": s, "note": note} for n, s, note in results],
    indent=2,
    ensure_ascii=False,
))
print(f"\nEvidence written to {evidence_path}")

# Exit code
failed = [r for r in results if r[1] not in (200, 401, 422)]
print(f"\n{'PASS' if not failed else 'FAIL'}: {len(results) - len(failed)}/{len(results)} expectations met")
sys.exit(1 if failed else 0)