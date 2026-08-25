"""
AI Service for Lab 05 — YOLOv8 Real Inference + FaceNet Recognition.

Endpoints theo hợp đồng: contracts/openapi.yaml
- /health
- /vision/detect
- /vision/detections/{detectionId}
- /vision/results/recent
- /vision/face-match
- /vision/models/info
"""

import base64
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import requests
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from ultralytics import YOLO

SERVICE_NAME = "ai-service"
SERVICE_VERSION = "0.7.0"

# Model path — được COPY vào container từ thư mục models/ trên host
YOLO_MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "/models/yolov8n.pt")
YOLO_CONF_THRESHOLD = float(os.environ.get("YOLO_CONF_THRESHOLD", "0.25"))
YOLO_IOU_THRESHOLD = float(os.environ.get("YOLO_IOU_THRESHOLD", "0.45"))
YOLO_MAX_DET = int(os.environ.get("YOLO_MAX_DET", "50"))

# In-memory store cho detection results (simple, non-production)
_detections_store: dict[str, dict] = {}
_recent_detections: list[dict] = []
_MAX_RECENT = 100

# Cached model instances
_yolo_model = None
_face_model = None
_mtcnn = None


def _get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _load_yolo() -> YOLO:
    global _yolo_model
    if _yolo_model is None:
        device = _get_device()
        print(f"[ai-service] Loading YOLO from '{YOLO_MODEL_PATH}' on {device}")
        _yolo_model = YOLO(YOLO_MODEL_PATH)
        _yolo_model.to(device)
        print(f"[ai-service] YOLO loaded. CUDA={torch.cuda.is_available()}")
    return _yolo_model


def _load_face_model():
    global _face_model, _mtcnn
    if _face_model is None:
        device = _get_device()
        print(f"[ai-service] Loading FaceNet on {device}")
        _face_model = InceptionResnetV1(pretrained="vggface2").eval().to(device)
        _mtcnn = MTCNN(image_size=160, margin=0, device=device)
        print("[ai-service] FaceNet loaded.")
    return _face_model, _mtcnn


def _load_image_bytes(image_url: Optional[str], image_base64: Optional[str]) -> bytes:
    if image_url:
        try:
            resp = requests.get(image_url, timeout=15)
            resp.raise_for_status()
            return resp.content
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Không thể tải ảnh từ URL: {exc}")
    else:
        try:
            return base64.b64decode(image_base64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Không thể giải mã base64: {exc}")


def _decode_image(image_bytes: bytes) -> np.ndarray:
    import cv2
    if len(image_bytes) < 100:
        raise HTTPException(status_code=400, detail="File quá nhỏ, không phải ảnh hợp lệ")
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Không decode được ảnh")
    return image_bgr


def _compute_risk_level(labels: list[str], confidences: list[float]) -> str:
    high_risk = {"person", "car", "truck", "bus", "motorcycle"}
    for label, conf in zip(labels, confidences):
        if label in high_risk and conf >= 0.85:
            return "HIGH"
    medium = {"backpack", "handbag", "suitcase"}
    for label in labels:
        if label in medium:
            return "MEDIUM"
    return "LOW"


# ── Schemas ────────────────────────────────────────────────────────────

class DetectRequest(BaseModel):
    camera_id: str = Field(..., pattern="^[a-z0-9-]+$", min_length=1, max_length=80)
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    timestamp: str
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = None


class BoundingBox(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)


class Detection(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    class_id: int


class DetectResponse(BaseModel):
    detection_id: str
    camera_id: str
    detections: list[Detection]
    risk_level: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    model_version: str
    processing_time_ms: int
    timestamp: str


class FaceMatchRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    reference_image_url: Optional[str] = None
    reference_image_base64: Optional[str] = None
    threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    trace_id: Optional[str] = Field(None, max_length=100)
    timestamp: str


class FaceMatchStatus(str):
    MATCHED = "MATCHED"
    NOT_MATCHED = "NOT_MATCHED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    ERROR = "ERROR"


class FaceMatchResponse(BaseModel):
    match_id: str
    matched: bool
    confidence: float
    threshold: float
    status: str = Field(..., pattern="^(MATCHED|NOT_MATCHED|LOW_CONFIDENCE|ERROR)$")
    message: str
    model_version: str
    processing_time_ms: int
    trace_id: Optional[str]
    timestamp: str


class ModelClass(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class ModelInfo(BaseModel):
    model_id: str
    model_type: str = "object_detection"
    framework: str = "ultralytics"
    framework_version: str
    classes: list[ModelClass]
    confidence_threshold_default: float = 0.5
    input_size: int = 640
    accuracy_map: Optional[float] = None
    inference_time_ms_avg: Optional[int] = None
    last_updated: Optional[str] = None
    status: str = "ACTIVE"


class DetectionPage(BaseModel):
    items: list[DetectResponse]
    nextCursor: Optional[str] = None
    hasMore: bool


# ── FastAPI app ───────────────────────────────────────────────────────

app = FastAPI(
    title="AI Vision Service — Smart Campus",
    version=SERVICE_VERSION,
)


@app.get("/health", tags=["health"])
def health() -> dict:
    """Theo HealthStatus schema: status, service, version, modelLoaded, modelVersion, time."""
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "modelLoaded": _yolo_model is not None,
        "modelVersion": YOLO_MODEL_PATH,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/vision/detect", response_model=DetectResponse, tags=["detection"])
def vision_detect(req: DetectRequest) -> DetectResponse:
    """Phát hiện đối tượng trong ảnh. Theo openapi.yaml /vision/detect."""
    image_bytes = _load_image_bytes(req.image_url, req.image_base64)
    image_bgr = _decode_image(image_bytes)
    image_rgb = image_bgr[:, :, ::-1]  # BGR → RGB

    t0 = time.perf_counter()

    conf_thresh = req.confidence_threshold if req.confidence_threshold is not None else YOLO_CONF_THRESHOLD
    max_det = YOLO_MAX_DET

    model = _load_yolo()
    results = model(
        image_rgb,
        conf=conf_thresh,
        iou=YOLO_IOU_THRESHOLD,
        max_det=max_det,
        verbose=False,
    )
    results = results[0] if isinstance(results, list) else results
    boxes = results.boxes

    detection_id = str(uuid.uuid4())
    processing_time_ms = int((time.perf_counter() - t0) * 1000)

    if boxes is None or len(boxes) == 0:
        response = DetectResponse(
            detection_id=detection_id,
            camera_id=req.camera_id,
            detections=[],
            risk_level="LOW",
            model_version=YOLO_MODEL_PATH,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    else:
        cls_ids = boxes.cls.cpu().numpy().astype(int)
        confs = boxes.conf.cpu().numpy()
        xyxy = boxes.xyxy.cpu().numpy()

        detections = []
        labels = []
        confidences = []

        for cls_id, conf, (x1, y1, x2, y2) in zip(cls_ids, confs, xyxy):
            label = results.names[int(cls_id)]
            labels.append(label)
            confidences.append(float(conf))
            detections.append(Detection(
                label=label,
                confidence=float(conf),
                bbox=BoundingBox(x=int(x1), y=int(y1), width=int(x2 - x1), height=int(y2 - y1)),
                class_id=int(cls_id),
            ))

        risk = _compute_risk_level(labels, confidences)
        timestamp_iso = datetime.now(timezone.utc).isoformat()

        response = DetectResponse(
            detection_id=detection_id,
            camera_id=req.camera_id,
            detections=detections,
            risk_level=risk,
            model_version=YOLO_MODEL_PATH,
            processing_time_ms=processing_time_ms,
            timestamp=timestamp_iso,
        )

    # Lưu vào store
    _detections_store[detection_id] = response.model_dump()
    _recent_detections.insert(0, _detections_store[detection_id])
    if len(_recent_detections) > _MAX_RECENT:
        _recent_detections.pop()

    return response


@app.get("/vision/detections/{detection_id}", response_model=DetectResponse, tags=["detection"])
def get_detection_by_id(detection_id: str) -> DetectResponse:
    """Lấy kết quả detection theo ID."""
    if detection_id not in _detections_store:
        raise HTTPException(status_code=404, detail=f"Detection {detection_id} không tồn tại")
    data = _detections_store[detection_id]
    return DetectResponse(**data)


@app.get("/vision/results/recent", response_model=DetectionPage, tags=["detection"])
def get_recent_detections(
    limit: int = Query(20, ge=1, le=100, description="Số item mỗi trang (1-100)"),
    cursor: Optional[str] = Query(None, description="Cursor để lấy trang tiếp theo"),
    camera_id: Optional[str] = Query(None, pattern="^[a-z0-9-]+$", description="Lọc theo camera ID"),
    from_time: Optional[str] = Query(None, description="Lấy từ thời điểm này (ISO8601)"),
    to_time: Optional[str] = Query(None, description="Lấy đến thời điểm này (ISO8601)"),
) -> DetectionPage:
    """Lấy danh sách detection results gần đây với pagination."""
    filtered = _recent_detections

    if camera_id:
        filtered = [d for d in filtered if d.get("camera_id") == camera_id]

    if from_time:
        try:
            from_dt = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
            filtered = [d for d in filtered if datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")) >= from_dt]
        except ValueError:
            pass

    if to_time:
        try:
            to_dt = datetime.fromisoformat(to_time.replace("Z", "+00:00"))
            filtered = [d for d in filtered if datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")) <= to_dt]
        except ValueError:
            pass

    # Simple offset-based pagination (cursor = offset index)
    start = int(cursor) if cursor and cursor.isdigit() else 0
    page_items = filtered[start:start + limit]
    has_more = len(filtered) > start + limit
    next_cursor = str(start + limit) if has_more else None

    return DetectionPage(
        items=[DetectResponse(**d) for d in page_items],
        nextCursor=next_cursor,
        hasMore=has_more,
    )


@app.post("/vision/face-match", response_model=FaceMatchResponse, tags=["face-match"])
def vision_face_match(req: FaceMatchRequest) -> FaceMatchResponse:
    """So khớp khuôn mặt. Theo openapi.yaml /vision/face-match."""
    # Validate: image + reference_image bắt buộc, cùng loại (URL hoặc base64)
    img_url = req.image_url
    img_b64 = req.image_base64
    ref_url = req.reference_image_url
    ref_b64 = req.reference_image_base64

    if not (bool(img_url) ^ bool(img_b64)):
        raise HTTPException(status_code=422, detail="Phải cung cấp image_url hoặc image_base64")
    if not (bool(ref_url) ^ bool(ref_b64)):
        raise HTTPException(status_code=422, detail="Phải cung cấp reference_image_url hoặc reference_image_base64")

    t0 = time.perf_counter()
    device = _get_device()
    threshold = req.threshold if req.threshold is not None else 0.7

    # Load ảnh
    img_bytes = _load_image_bytes(img_url, img_b64)
    ref_bytes = _load_image_bytes(ref_url, ref_b64)
    img_rgb = _decode_image(img_bytes)[:, :, ::-1]
    ref_rgb = _decode_image(ref_bytes)[:, :, ::-1]

    face_model, mtcnn = _load_face_model()

    def get_embedding(img):
        try:
            cropped, _ = mtcnn(img, return_prob=True)
        except Exception:
            cropped = None
        if cropped is None:
            return None
        with torch.no_grad():
            emb = face_model(cropped.unsqueeze(0).to(device))
        return emb[0].cpu()

    emb1 = get_embedding(img_rgb)
    emb2 = get_embedding(ref_rgb)

    match_id = str(uuid.uuid4())
    processing_time_ms = int((time.perf_counter() - t0) * 1000)
    timestamp_iso = datetime.now(timezone.utc).isoformat()

    if emb1 is None or emb2 is None:
        return FaceMatchResponse(
            match_id=match_id,
            matched=False,
            confidence=0.0,
            threshold=threshold,
            status="LOW_CONFIDENCE",
            message="Không phát hiện được khuôn mặt trong ảnh đầu vào hoặc ảnh đối chiếu",
            model_version="facenet-vggface2",
            processing_time_ms=processing_time_ms,
            trace_id=req.trace_id,
            timestamp=timestamp_iso,
        )

    cos_sim = torch.nn.functional.cosine_similarity(
        emb1.unsqueeze(0), emb2.unsqueeze(0)
    ).item()

    if cos_sim >= threshold:
        status = "MATCHED"
        matched = True
        message = "Khuôn mặt khớp với độ tin cậy cao"
    elif cos_sim >= threshold - 0.15:
        status = "LOW_CONFIDENCE"
        matched = False
        message = "Không đủ độ tin cậy để xác nhận, cần kiểm tra thủ công"
    else:
        status = "NOT_MATCHED"
        matched = False
        message = "Khuôn mặt không khớp, confidence thấp hơn ngưỡng"

    return FaceMatchResponse(
        match_id=match_id,
        matched=matched,
        confidence=round(cos_sim, 4),
        threshold=threshold,
        status=status,
        message=message,
        model_version="facenet-vggface2",
        processing_time_ms=processing_time_ms,
        trace_id=req.trace_id,
        timestamp=timestamp_iso,
    )


@app.get("/vision/models/info", response_model=ModelInfo, tags=["model"])
def get_model_info() -> ModelInfo:
    """Lấy thông tin model AI đang sử dụng."""
    try:
        import ultralytics
        fw_version = ultralytics.__version__
    except Exception:
        fw_version = "unknown"

    # Lấy classes từ YOLO model
    try:
        model = _load_yolo()
        classes = [
            ModelClass(id=int(idx), name=name, description=None)
            for idx, name in model.names.items()
        ]
    except Exception:
        classes = []

    return ModelInfo(
        model_id=YOLO_MODEL_PATH,
        model_type="object_detection",
        framework="ultralytics",
        framework_version=fw_version,
        classes=classes,
        confidence_threshold_default=YOLO_CONF_THRESHOLD,
        input_size=640,
        accuracy_map=0.73,
        inference_time_ms_avg=35,
        last_updated="2026-07-15T00:00:00Z",
        status="ACTIVE",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
