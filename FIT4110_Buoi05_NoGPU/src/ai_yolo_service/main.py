"""AI YOLOv8 Service — Smart Campus (FIT4110 Buổi 05, NoGPU).

Container này chạy YOLOv8n trên CPU và cung cấp 2 endpoint:
  - GET  /health   → liveness + model loaded flag
  - POST /predict  → nhận ảnh (base64 hoặc URL), trả về detections

Service được API chính (ai-vision) gọi qua HTTP qua mạng nội bộ team-internal.
Đây là minh họa cho yêu cầu Buổi 05 "API gọi được AI qua nội bộ".

Khi môi trường không có weights thật (offline lab), service vẫn hoạt động ở
chế độ stub deterministic để giữ smoke test xanh.
"""
from __future__ import annotations

import base64
import hashlib
import io
import logging
import os
import time
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

LOGGER = logging.getLogger("ai_yolo")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

SERVICE_NAME = os.environ.get("SERVICE_NAME", "ai-yolo")
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "0.5.0")
YOLO_MODEL_NAME = os.environ.get("YOLO_MODEL_NAME", "yolov8n")
YOLO_INPUT_SIZE = int(os.environ.get("YOLO_INPUT_SIZE", "640"))
YOLO_CONFIDENCE_DEFAULT = float(os.environ.get("YOLO_CONFIDENCE_DEFAULT", "0.5"))
YOLO_WEIGHTS_PATH = os.environ.get("YOLO_WEIGHTS_PATH", f"{YOLO_MODEL_NAME}.pt")

COCO_LABELS: dict[int, str] = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus",
    7: "truck", 15: "cat", 16: "dog", 24: "backpack", 26: "handbag",
    27: "tie", 39: "bottle", 41: "cup", 56: "chair", 57: "couch",
    60: "dining table", 62: "tv", 67: "dining table",
}

app = FastAPI(
    title="AI YOLOv8 Service (NoGPU)",
    version=SERVICE_VERSION,
    description="FIT4110 Buổi 05 — YOLOv8 inference (CPU), đứng sau ai-vision API.",
)


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_url: str | None = None
    image_base64: str | None = None
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    model_name: str | None = None
    input_size: int | None = Field(default=None, ge=64, le=2048)

    @field_validator("image_url")
    @classmethod
    def _image_url_must_be_http(cls, v: str | None) -> str | None:
        # Theo hợp đồng Buổi 02, URL không hợp lệ là lỗi client 422, không để lọt xuống fetch.
        if v is None:
            return None
        if not isinstance(v, str) or not v.startswith(("http://", "https://")):
            raise ValueError(
                "image_url phải là URL tuyệt đối bắt đầu bằng http:// hoặc https://"
            )
        return v


class DetectionOut(BaseModel):
    label: str
    confidence: float
    class_id: int
    bbox: BoundingBox


class PredictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    model_version: str
    inference_time_ms: int
    mode: Literal["inproc", "stub"]
    detections: list[DetectionOut]


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: str
    version: str
    mode: Literal["inproc", "stub"]
    model_loaded: bool
    model_name: str
    weights_path: str
    time: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _try_load_model():
    """Thử load YOLOv8 thật; trả về None nếu thiếu weights hoặc thiếu ultralytics."""
    if not os.path.exists(YOLO_WEIGHTS_PATH):
        LOGGER.info("YOLO weights %s không tồn tại — dùng stub", YOLO_WEIGHTS_PATH)
        return None
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        LOGGER.info("Thiếu ultralytics — dùng stub")
        return None
    try:
        model = YOLO(YOLO_WEIGHTS_PATH)
        LOGGER.info("Đã load YOLO weights từ %s", YOLO_WEIGHTS_PATH)
        return model
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Không load được YOLO (%s) — dùng stub", exc)
        return None


_MODEL = _try_load_model()


def _stub_detections(image_digest: str, threshold: float) -> list[DetectionOut]:
    digest_bytes = hashlib.sha256(image_digest.encode()).digest()
    n = (digest_bytes[0] % 3) + 1
    out: list[DetectionOut] = []
    class_ids = list(COCO_LABELS.keys())
    for i in range(n):
        offset = i * 4
        conf = 0.55 + ((digest_bytes[offset + 1] % 40) / 100.0)
        if conf < threshold:
            continue
        cls = class_ids[digest_bytes[offset + 2] % len(class_ids)]
        out.append(
            DetectionOut(
                label=COCO_LABELS[cls],
                confidence=round(min(conf, 0.99), 4),
                class_id=cls,
                bbox=BoundingBox(
                    x=50 + (digest_bytes[offset + 3] % 300),
                    y=30 + (digest_bytes[offset] % 200),
                    width=60 + (digest_bytes[offset + 1] % 120),
                    height=80 + (digest_bytes[offset + 2] % 160),
                ),
            )
        )
    return out


def _decode_image_b64(image_b64: str):
    import numpy as np
    from PIL import Image

    raw = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    return np.array(img)


def _decode_image_bytes(raw: bytes):
    """Decode JPEG/PNG/WebP bytes thành numpy RGB array."""
    import numpy as np
    from PIL import Image

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    return np.array(img)


def _model_to_detections(results) -> list[DetectionOut]:
    out: list[DetectionOut] = []
    for r in results:
        names = r.names if hasattr(r, "names") else COCO_LABELS
        for box in r.boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            xyxy = box.xyxy[0].tolist()
            out.append(
                DetectionOut(
                    label=str(names.get(cls_id, "object")),
                    confidence=round(conf, 4),
                    class_id=cls_id,
                    bbox=BoundingBox(
                        x=int(max(0, xyxy[0])),
                        y=int(max(0, xyxy[1])),
                        width=int(max(1, xyxy[2] - xyxy[0])),
                        height=int(max(1, xyxy[3] - xyxy[1])),
                    ),
                )
            )
    return out


def _model_predict(req: PredictRequest) -> tuple[list[DetectionOut], int]:
    """Chạy model thật hoặc fallback stub. Trả về (detections, inference_ms)."""
    threshold = req.confidence_threshold if req.confidence_threshold is not None else YOLO_CONFIDENCE_DEFAULT
    input_size = req.input_size or YOLO_INPUT_SIZE

    if _MODEL is None:
        digest = req.image_base64 or req.image_url or "empty"
        return _stub_detections(digest, threshold), 15

    if not req.image_base64:
        # Phải fetch ảnh từ URL trước khi predict. URL sai / ảnh hỏng phải fail-fast
        # (Bad Gateway) chứ không được ngầm fallback sang stub — nếu không
        # client sẽ thấy detection giả mà tưởng model thật đã chạy.
        digest = req.image_url or "no-image"
        try:
            import httpx

            img_resp = httpx.get(req.image_url, timeout=10.0, follow_redirects=True)
            img_resp.raise_for_status()
            arr = _decode_image_bytes(img_resp.content)
        except httpx.HTTPStatusError as exc:
            LOGGER.warning(
                "URL trả về HTTP %s — fail-fast (không fallback stub)",
                exc.response.status_code,
            )
            raise HTTPException(
                status_code=502,
                detail=f"image_url không truy cập được: HTTP {exc.response.status_code}",
            ) from exc
        except httpx.HTTPError as exc:
            LOGGER.warning("Fetch URL thất bại (%s) — fail-fast", exc)
            raise HTTPException(
                status_code=502,
                detail=f"image_url fetch thất bại: {exc}",
            ) from exc

        started = time.perf_counter()
        results = _MODEL.predict(source=arr, conf=threshold, verbose=False, imgsz=input_size)
        elapsed = int((time.perf_counter() - started) * 1000)
        out = _model_to_detections(results)
        if not out:
            # Model thật không thấy object nào — trả rỗng (đúng nghiệp vụ,
            # không được ngầm bịa detection để smoke test xanh).
            return [], elapsed
        return out, elapsed

    try:
        arr = _decode_image_b64(req.image_base64)
    except Exception as exc:  # noqa: BLE001
        # base64 hỏng là lỗi client — trả 400, không stub.
        LOGGER.warning("Decode base64 thất bại (%s)", exc)
        raise HTTPException(
            status_code=400,
            detail=f"image_base64 không decode được: {exc}",
        ) from exc

    started = time.perf_counter()
    results = _MODEL.predict(source=arr, conf=threshold, verbose=False, imgsz=input_size)
    elapsed = int((time.perf_counter() - started) * 1000)
    out = _model_to_detections(results)
    if not out:
        # Model thật không thấy object nào — trả rỗng (đúng nghiệp vụ).
        return [], elapsed
    return out, elapsed


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        mode="inproc" if _MODEL is not None else "stub",
        model_loaded=_MODEL is not None,
        model_name=YOLO_MODEL_NAME,
        weights_path=YOLO_WEIGHTS_PATH if _MODEL is not None else "(stub-fallback)",
        time=_now_iso(),
    )


@app.post("/predict", response_model=PredictResponse, tags=["inference"])
async def predict(req: PredictRequest) -> PredictResponse:
    if not (bool(req.image_url) ^ bool(req.image_base64)):
        raise HTTPException(status_code=422, detail="Phải cung cấp image_url HOẶC image_base64 (XOR)")

    detections, elapsed_ms = _model_predict(req)
    return PredictResponse(
        model_id=f"{YOLO_MODEL_NAME}-cpu-{SERVICE_VERSION}",
        model_version=f"{YOLO_MODEL_NAME}-cpu-v1.0",
        inference_time_ms=elapsed_ms,
        mode="inproc" if _MODEL is not None else "stub",
        detections=detections,
    )