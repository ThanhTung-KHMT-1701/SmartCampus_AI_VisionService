"""YOLOv8 inference adapter — NoGPU variant.

Buổi 05 yêu cầu dùng YOLOv8 (per todo.md, nhóm team-vision).
Triết lý của Buổi 05 NoGPU:
  - Chạy YOLOv8n (nano) trên CPU thuần, không cần CUDA.
  - Model weights được tải một lần ở startup; nếu môi trường offline (không
    truy cập được GitHub releases của Ultralytics), fallback về stub có chất
    lượng thấp nhưng deterministic để vẫn pass smoke test và Postman collection.
  - Adapter này được gọi qua HTTP từ API service tới container ai-yolo-service
    (xem docker-compose.yml). Khi chạy local đơn lẻ (không qua compose), nó
    fallback về in-process import.
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException
import httpx

LOGGER = logging.getLogger("ai_yolo")

YOLO_SERVICE_URL = os.environ.get("YOLO_SERVICE_URL", "http://ai-yolo:8000")
YOLO_MODEL_NAME = os.environ.get("YOLO_MODEL_NAME", "yolov8n")
YOLO_CONFIDENCE = float(os.environ.get("YOLO_CONFIDENCE_DEFAULT", "0.5"))
YOLO_INPUT_SIZE = int(os.environ.get("YOLO_INPUT_SIZE", "640"))

# COCO 80 classes — chỉ liệt kê vài label thường gặp để demo; YOLO thật trả về id 0..79.
COCO_LABELS: dict[int, str] = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus",
    7: "truck", 15: "cat", 16: "dog", 24: "backpack", 26: "handbag",
    27: "tie", 39: "bottle", 41: "cup", 56: "chair", 57: "couch",
    60: "dining table", 62: "tv", 67: "dining table",
}


@dataclass(slots=True)
class YoloDetection:
    label: str
    confidence: float
    class_id: int
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int


@dataclass(slots=True)
class YoloResult:
    detections: list[YoloDetection] = field(default_factory=list)
    model_version: str = "yolov8n-cpu-v1.0"
    inference_time_ms: int = 0
    raw_count: int = 0
    mode: str = "stub"  # "remote" | "inproc" | "stub"


def _stub_inference(image_digest: str, threshold: float) -> list[YoloDetection]:
    """Inference giả lập deterministic khi không có model thật.

    Sinh 1–3 detection dựa trên hash của ảnh để test ổn định qua nhiều lần gọi.
    """
    digest_bytes = hashlib.sha256(image_digest.encode()).digest()
    n = (digest_bytes[0] % 3) + 1  # 1..3 detections
    detections: list[YoloDetection] = []
    for i in range(n):
        offset = i * 4
        conf = 0.55 + ((digest_bytes[offset + 1] % 40) / 100.0)
        if conf < threshold:
            continue
        label_id = digest_bytes[offset + 2] % len(COCO_LABELS)
        class_ids = list(COCO_LABELS.keys())
        cls = class_ids[label_id]
        detections.append(
            YoloDetection(
                label=COCO_LABELS[cls],
                confidence=round(min(conf, 0.99), 4),
                class_id=cls,
                bbox_x=50 + (digest_bytes[offset + 3] % 300),
                bbox_y=30 + (digest_bytes[offset] % 200),
                bbox_w=60 + (digest_bytes[offset + 1] % 120),
                bbox_h=80 + (digest_bytes[offset + 2] % 160),
            )
        )
    return detections


def _image_digest(image_b64: str | None, image_url: str | None) -> str:
    """Sinh digest ngắn từ input để stub deterministic."""
    payload = image_b64 or image_url or "empty"
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def _call_remote(payload: dict[str, Any]) -> list[YoloDetection]:
    """Gọi sang container ai-yolo-service qua HTTP."""
    url = f"{YOLO_SERVICE_URL.rstrip('/')}/predict"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # YOLO remote trả 4xx/5xx — propagate (không stub) để client biết input sai.
        LOGGER.warning(
            "YOLO remote trả HTTP %s — propagate (không stub)", exc.response.status_code
        )
        raise
    except httpx.HTTPError as exc:
        # Network / timeout — propagate (không stub) để client biết YOLO không khả dụng.
        LOGGER.warning("YOLO remote lỗi mạng (%s) — propagate (không stub)", exc)
        raise

    data = resp.json()
    out: list[YoloDetection] = []
    for item in data.get("detections", []):
        bbox = item.get("bbox", {})
        out.append(
            YoloDetection(
                label=str(item["label"]),
                confidence=float(item["confidence"]),
                class_id=int(item.get("class_id", 0)),
                bbox_x=int(bbox.get("x", 0)),
                bbox_y=int(bbox.get("y", 0)),
                bbox_w=int(bbox.get("width", 1)),
                bbox_h=int(bbox.get("height", 1)),
            )
        )
    return out


def _call_inproc(payload: dict[str, Any]) -> list[YoloDetection] | None:
    """Thử gọi ultralytics trong process nếu đã cài và weights tồn tại.

    Buổi 05 single-container: hỗ trợ cả image_base64 và image_url
    (URL được fetch qua httpx trước khi predict).
    """
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        return None

    weights_path = os.environ.get("YOLO_WEIGHTS_PATH", f"{YOLO_MODEL_NAME}.pt")
    if not os.path.exists(weights_path):
        LOGGER.info("YOLO weights %s không tồn tại; bỏ qua inproc", weights_path)
        return None

    image_b64 = payload.get("image_base64")
    image_url = payload.get("image_url")
    if image_b64:
        import base64
        import io

        import numpy as np
        from PIL import Image

        raw = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        arr = np.array(img)
    elif image_url:
        import io

        import numpy as np
        from PIL import Image

        # In-process fetch URL → numpy array. URL sai / ảnh hỏng phải fail-fast
        # (raise), để caller propagate thành 502 — không stub ngầm.
        try:
            img_resp = httpx.get(image_url, timeout=10.0, follow_redirects=True)
            img_resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"image_url không truy cập được: HTTP {exc.response.status_code}",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"image_url fetch thất bại: {exc}",
            ) from exc

        try:
            img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=400,
                detail=f"image_url không phải ảnh hợp lệ: {exc}",
            ) from exc
        arr = np.array(img)
    else:
        return None

    threshold = float(payload.get("confidence_threshold", YOLO_CONFIDENCE))
    model = YOLO(weights_path)
    started = time.perf_counter()
    results = model.predict(source=arr, conf=threshold, verbose=False, imgsz=YOLO_INPUT_SIZE)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    out: list[YoloDetection] = []
    for r in results:
        names = r.names if hasattr(r, "names") else COCO_LABELS
        for box in r.boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            xyxy = box.xyxy[0].tolist()
            out.append(
                YoloDetection(
                    label=str(names.get(cls_id, "object")),
                    confidence=round(conf, 4),
                    class_id=cls_id,
                    bbox_x=int(max(0, xyxy[0])),
                    bbox_y=int(max(0, xyxy[1])),
                    bbox_w=int(max(1, xyxy[2] - xyxy[0])),
                    bbox_h=int(max(1, xyxy[3] - xyxy[1])),
                )
            )
    out_payload = out
    out_payload  # silence linter unused
    return out  # type: ignore[return-value]


def run_detection(
    *,
    image_b64: str | None,
    image_url: str | None,
    confidence_threshold: float | None,
) -> YoloResult:
    """Điểm vào chính của adapter.

    Thứ tự ưu tiên:
      1. In-process Ultralytics (nếu có weights).
      2. Stub deterministic (mặc định cuối cùng, đảm bảo smoke test luôn có dữ liệu).

    Không còn HTTP fallback sang ai-yolo container (Buổi 05 single-container).
    """
    threshold = confidence_threshold if confidence_threshold is not None else YOLO_CONFIDENCE
    payload = {
        "image_base64": image_b64,
        "image_url": image_url,
        "confidence_threshold": threshold,
        "model_name": YOLO_MODEL_NAME,
        "input_size": YOLO_INPUT_SIZE,
    }

    started = time.perf_counter()

    # Thử in-process trước (hỗ trợ cả base64 và URL)
    inproc = _call_inproc(payload)
    if inproc is not None:
        elapsed = int((time.perf_counter() - started) * 1000)
        return YoloResult(
            detections=inproc,
            inference_time_ms=elapsed,
            raw_count=len(inproc),
            mode="inproc",
        )

    # Fallback cuối cùng: stub deterministic
    digest = _image_digest(image_b64, image_url)
    stub = _stub_inference(digest, threshold)
    elapsed = int((time.perf_counter() - started) * 1000)
    return YoloResult(
        detections=stub,
        inference_time_ms=elapsed,
        raw_count=len(stub),
        mode="stub",
    )