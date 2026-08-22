"""
AI Service for Lab 05 — YOLOv8 Real Inference.

Chạy YOLOv8 inference thực sự trên GPU CUDA.
Model được COPY vào container từ thư mục models/ trong project (pre-downloaded).
Nếu GPU không khả dụng, fallback về CPU.
"""

import os
import time
from io import BytesIO
from typing import Optional

import requests
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from ultralytics import YOLO

SERVICE_NAME = "ai-service"
SERVICE_VERSION = "0.6.0"

# Model path — được COPY vào container từ thư mục models/ trên host
YOLO_MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "/models/yolov8n.pt")
YOLO_CONF_THRESHOLD = float(os.environ.get("YOLO_CONF_THRESHOLD", "0.25"))
YOLO_IOU_THRESHOLD = float(os.environ.get("YOLO_IOU_THRESHOLD", "0.45"))
YOLO_MAX_DET = int(os.environ.get("YOLO_MAX_DET", "50"))

# Cached model instance
_model = None


def _get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _load_model() -> YOLO:
    global _model
    if _model is None:
        device = _get_device()
        print(f"[ai-service] Loading YOLO model from '{YOLO_MODEL_PATH}' on device: {device}")
        _model = YOLO(YOLO_MODEL_PATH)
        _model.to(device)
        print(f"[ai-service] Model loaded. CUDA available: {torch.cuda.is_available()}")
    return _model


class PredictRequest(BaseModel):
    image_url: Optional[str] = Field(None, description="URL của ảnh cần nhận diện")
    image_base64: Optional[str] = Field(None, description="Ảnh mã hóa base64")
    confidence_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Ngưỡng confidence (mặc định: 0.25)"
    )
    max_detections: Optional[int] = Field(
        None, ge=1, le=300,
        description="Số object tối đa trả về (mặc định: 50)"
    )


class Prediction(BaseModel):
    objects: list[str]
    confidence: list[float]
    labels: list[str]
    scores: list[float]
    model: str
    device: str
    inference_time_ms: float


app = FastAPI(
    title="FIT4110 Lab 05 - AI Service (YOLOv8)",
    version=SERVICE_VERSION,
    description="Real YOLOv8 inference service with CUDA GPU support.",
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "model": YOLO_MODEL_PATH,
        "device": _get_device(),
        "cuda_available": torch.cuda.is_available(),
    }


@app.post("/predict", response_model=Prediction)
def predict(req: PredictRequest) -> Prediction:
    # ── 1. Validate input ───────────────────────────────────────────
    if not (bool(req.image_url) ^ bool(req.image_base64)):
        raise HTTPException(
            status_code=422,
            detail="Phải cung cấp image_url hoặc image_base64 (không đồng thời cả hai)",
        )

    # ── 2. Load image ──────────────────────────────────────────────
    if req.image_url:
        try:
            resp = requests.get(req.image_url, timeout=15)
            resp.raise_for_status()
            image_bytes = resp.content
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Không thể tải ảnh từ URL: {exc}",
            )
    else:
        try:
            import base64 as _b64

            image_bytes = _b64.b64decode(req.image_base64)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Không thể giải mã base64: {exc}",
            )

    if len(image_bytes) < 100:
        raise HTTPException(status_code=400, detail="File quá nhỏ, không phải ảnh hợp lệ")

    image_stream = BytesIO(image_bytes)
    import numpy as np, cv2
    nparr = np.frombuffer(image_stream.getvalue(), np.uint8)
    image_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # ── 3. Run inference ───────────────────────────────────────────
    t0 = time.perf_counter()

    conf_thresh = req.confidence_threshold if req.confidence_threshold is not None else YOLO_CONF_THRESHOLD
    max_det = req.max_detections if req.max_detections is not None else YOLO_MAX_DET

    model = _load_model()
    results = model(
        image_np,
        conf=conf_thresh,
        iou=YOLO_IOU_THRESHOLD,
        max_det=max_det,
        verbose=False,
        stream=False,
    )

    inference_ms = (time.perf_counter() - t0) * 1000

    # ── 4. Extract results ────────────────────────────────────────
    # model() với stream=False trả về list chứa 1 Results object
    results = results[0] if isinstance(results, list) else results
    boxes = results.boxes
    if boxes is None or len(boxes) == 0:
        return Prediction(
            objects=[],
            confidence=[],
            labels=[],
            scores=[],
            model=YOLO_MODEL_PATH,
            device=_get_device(),
            inference_time_ms=round(inference_ms, 2),
        )

    labels = [results.names[int(cls)] for cls in boxes.cls.cpu().numpy()]
    confidences = boxes.conf.cpu().numpy().tolist()

    return Prediction(
        objects=labels,
        confidence=confidences,
        labels=labels,
        scores=confidences,
        model=YOLO_MODEL_PATH,
        device=_get_device(),
        inference_time_ms=round(inference_ms, 2),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
