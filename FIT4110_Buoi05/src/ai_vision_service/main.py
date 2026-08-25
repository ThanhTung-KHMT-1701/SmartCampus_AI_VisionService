"""AI Vision Service — Smart Campus.

Tuân thủ hợp đồng contracts/ai-vision.openapi.yaml (FIT4110 Buổi 2/3).

Service thật chạy inference bằng stub (mô phỏng model AI). Có thể thay thế
bằng mô hình YOLO thật bằng cách sửa hàm `infer_detections`.
"""
from __future__ import annotations

import asyncio
import base64
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .schemas import (
    BoundingBox,
    Detection,
    DetectRequest,
    DetectResponse,
    DetectionPage,
    FaceMatchRequest,
    FaceMatchResponse,
    HealthStatus,
    ModelInfo,
    ProblemDetails,
)
from .store import DetectionStore

app = FastAPI(
    title="AI Vision Service",
    version="1.0.0",
    description="FIT4110 - Smart Campus AI Vision (FIT4110_Buoi03_Postman_Mock_Testing).",
)

store = DetectionStore()

AUTH_TOKEN_ENV = "AI_VISION_AUTH_TOKEN"
DEFAULT_TOKEN = "local-dev-token-vision"

MODEL_VERSION = "yolov8n-v1.0"
FACE_MODEL_VERSION = "facenet-v1.2"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_auth(request: Request) -> None:
    """Kiểm tra Bearer token trừ khi endpoint được đánh dấu public."""
    expected = os.environ.get(AUTH_TOKEN_ENV, DEFAULT_TOKEN)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Bearer token",
        )
    token = auth[len("Bearer ") :].strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
        )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI mặc định trả {detail: [...]} cho 422. Rewrap thành ProblemDetails."""
    problem = ProblemDetails(
        type="https://ai-vision.campus.local/errors/validation",
        title="Dữ liệu không hợp lệ",
        status=422,
        detail="Payload không khớp schema",
        instance=None,
    )
    payload = problem.model_dump(exclude_none=True)
    payload["errors"] = [
        {"field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
         "code": err.get("type", "INVALID"),
         "message": err.get("msg", "")}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=payload,
        media_type="application/problem+json",
    )


@app.exception_handler(HTTPException)
async def problem_details_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Trả lỗi theo cấu trúc ProblemDetails (RFC 9457)."""
    problem = ProblemDetails(
        type=f"https://ai-vision.campus.local/errors/{exc.status_code}",
        title=exc.detail if isinstance(exc.detail, str) else "Lỗi",
        status=exc.status_code,
        detail=exc.detail if isinstance(exc.detail, str) else None,
        instance=None,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


@app.get("/health", response_model=HealthStatus, tags=["health"])
async def get_health() -> HealthStatus:
    return HealthStatus(
        status="ok",
        service="ai-vision",
        version="1.0.0",
        modelLoaded=True,
        modelVersion=MODEL_VERSION,
        time=_now_iso(),
    )


def _infer_detections(req: DetectRequest) -> list[Detection]:
    """Stub inference: trả về 1 detection mẫu nếu có ảnh hợp lệ.

    Có thể thay bằng YOLO thật (ultralytics) khi có weights.
    """
    if not (bool(req.image_url) ^ bool(req.image_base64)):
        raise HTTPException(
            status_code=422,
            detail="Phải cung cấp image_url hoặc image_base64 (mutually exclusive)",
        )
    return [
        Detection(
            label="person",
            confidence=0.95,
            bbox=BoundingBox(x=100, y=50, width=80, height=150),
            class_id=0,
        )
    ]


@app.post(
    "/vision/detect",
    response_model=DetectResponse,
    tags=["detection"],
)
async def detect_objects(req: DetectRequest, request: Request) -> JSONResponse:
    _require_auth(request)
    started = time.perf_counter()
    detections = _infer_detections(req)
    processing_ms = int((time.perf_counter() - started) * 1000) + 35  # cộng overhead giả lập

    detection_id = str(uuid.uuid4())
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"
    if len(detections) >= 5:
        risk_level = "HIGH"
    elif len(detections) >= 2:
        risk_level = "MEDIUM"

    response = DetectResponse(
        detection_id=detection_id,
        camera_id=req.camera_id,
        detections=detections,
        risk_level=risk_level,
        model_version=MODEL_VERSION,
        processing_time_ms=processing_ms,
        timestamp=_now_iso(),
    )
    store.add(response)
    payload = response.model_dump(mode="json")
    headers = {
        "X-Detection-Id": detection_id,
        "X-Processing-Time-Ms": str(processing_ms),
    }
    return JSONResponse(status_code=200, content=payload, headers=headers)


@app.get(
    "/vision/detections/{detection_id}",
    response_model=DetectResponse,
    tags=["detection"],
)
async def get_detection_by_id(detection_id: str, request: Request) -> DetectResponse:
    _require_auth(request)
    try:
        uuid.UUID(detection_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="detection_id phải là UUID") from exc

    record = store.get(detection_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Detection {detection_id} không tồn tại hoặc đã hết hạn",
        )
    return record


@app.get(
    "/vision/results/recent",
    response_model=DetectionPage,
    tags=["detection"],
)
async def get_recent_detections(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=200),
    camera_id: str | None = Query(None, pattern=r"^[a-z0-9-]+$"),
    from_time: str | None = Query(None, alias="from_time"),
    to_time: str | None = Query(None, alias="to_time"),
) -> DetectionPage:
    _require_auth(request)
    items, next_cursor, has_more = store.list_recent(
        limit=limit,
        camera_id=camera_id,
    )
    return DetectionPage(
        items=items,
        nextCursor=next_cursor,
        hasMore=has_more,
    )


@app.post(
    "/vision/face-match",
    response_model=FaceMatchResponse,
    tags=["face-match"],
)
async def face_match(req: FaceMatchRequest, request: Request) -> JSONResponse:
    _require_auth(request)
    has_query = bool(req.image_url) ^ bool(req.image_base64)
    has_ref = bool(req.reference_image_url) ^ bool(req.reference_image_base64)
    if not (has_query and has_ref):
        raise HTTPException(
            status_code=422,
            detail="Phải cung cấp image_url XOR image_base64 và reference tương ứng",
        )

    started = time.perf_counter()
    await asyncio.sleep(0)  # yield once để tương thích async
    processing_ms = int((time.perf_counter() - started) * 1000) + 88

    confidence = 0.93
    if req.threshold is not None and req.threshold >= 0.9:
        confidence = 0.45  # mô phỏng kém khớp khi threshold cao

    matched = confidence >= req.threshold
    if matched:
        status_value: Literal["MATCHED", "NOT_MATCHED", "LOW_CONFIDENCE", "ERROR"] = "MATCHED"
        message = "Khuôn mặt khớp với độ tin cậy cao"
    elif confidence >= 0.6:
        status_value = "LOW_CONFIDENCE"
        message = "Không đủ độ tin cậy để xác nhận, cần kiểm tra thủ công"
    else:
        status_value = "NOT_MATCHED"
        message = "Khuôn mặt không khớp, confidence thấp hơn ngưỡng"

    response = FaceMatchResponse(
        match_id=str(uuid.uuid4()),
        matched=matched,
        confidence=confidence,
        threshold=req.threshold,
        status=status_value,
        message=message,
        model_version=FACE_MODEL_VERSION,
        processing_time_ms=processing_ms,
        trace_id=req.trace_id,
        timestamp=_now_iso(),
    )
    headers = {"X-Trace-Id": req.trace_id or ""}
    return JSONResponse(
        status_code=200,
        content=response.model_dump(mode="json"),
        headers=headers,
    )


@app.get(
    "/vision/models/info",
    response_model=ModelInfo,
    tags=["model"],
)
async def get_model_info(request: Request) -> ModelInfo:
    _require_auth(request)
    return ModelInfo(
        model_id=MODEL_VERSION,
        model_type="object_detection",
        framework="ultralytics",
        framework_version="8.3.0",
        classes=[
            {"id": 0, "name": "person", "description": "Con người"},
            {"id": 2, "name": "car", "description": "Ô tô"},
            {"id": 3, "name": "motorcycle", "description": "Xe máy"},
            {"id": 15, "name": "cat", "description": "Mèo"},
            {"id": 16, "name": "dog", "description": "Chó"},
        ],
        confidence_threshold_default=0.5,
        input_size=640,
        accuracy_map=0.73,
        inference_time_ms_avg=35,
        last_updated="2026-07-15T00:00:00Z",
        status="ACTIVE",
    )
