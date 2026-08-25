"""AI Vision Service — Smart Campus (FIT4110 Buổi 05, NoGPU).

Stack:
  - FastAPI (REST) — kế thừa từ Buổi 04
  - MySQL 8.0 persistence (Buổi 05 NoGPU) — thay SQLite
  - YOLOv8 inference adapter — chạy in-process
  - Auth Bearer — giữ nguyên từ Buổi 02/03/04
  - /ready endpoint — dùng cho docker-compose readiness check
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .schemas import (
    BoundingBox,
    Detection,
    DetectRequest,
    DetectResponse,
    DetectionPage,
    DependencyHealth,
    FaceMatchRequest,
    FaceMatchResponse,
    HealthStatus,
    ModelInfo,
    ProblemDetails,
    ReadinessStatus,
)
from . import db
from . import yolo_adapter
from . import face_adapter

LOGGER = logging.getLogger("ai_vision")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

SERVICE_NAME = os.environ.get("SERVICE_NAME", "ai-vision")
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "0.5.0")
AUTH_TOKEN_ENV = "AI_VISION_AUTH_TOKEN"
DEFAULT_TOKEN = "local-dev-token-vision"
YOLO_SERVICE_URL = os.environ.get("YOLO_SERVICE_URL", "http://ai-yolo:8000")

app = FastAPI(
    title="AI Vision Service (NoGPU)",
    version=SERVICE_VERSION,
    description=(
        "FIT4110 Buổi 05 — Smart Campus AI Vision, tích hợp YOLOv8 NoGPU "
        "và docker-compose readiness."
    ),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _problem_400(*, instance: str, detail: str, field: str, code: str, message: str) -> dict:
    """Sinh RFC 7807 Problem+JSON đúng schema BadRequest trong OpenAPI Buổi 02."""
    return {
        "type": "https://ai-vision.campus.local/errors/validation",
        "title": "Dữ liệu không hợp lệ",
        "status": 400,
        "detail": detail,
        "instance": instance,
        "errors": [
            {"field": field, "code": code, "message": message},
        ],
    }


def _require_auth(request: Request) -> None:
    expected = os.environ.get(AUTH_TOKEN_ENV, DEFAULT_TOKEN)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Thiếu Bearer token")
    token = auth[len("Bearer ") :].strip()
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    problem = ProblemDetails(
        type="https://ai-vision.campus.local/errors/validation",
        title="Dữ liệu không hợp lệ",
        status=422,
        detail="Payload không khớp schema",
        instance=None,
    )
    payload = problem.model_dump(exclude_none=True)
    payload["errors"] = [
        {
            "field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
            "code": err.get("type", "INVALID"),
            "message": err.get("msg", ""),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=payload,
        media_type="application/problem+json",
    )


@app.exception_handler(HTTPException)
async def problem_details_handler(_: Request, exc: HTTPException) -> JSONResponse:
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


@app.get("/health", response_model=HealthStatus, tags=["system"])
async def get_health() -> HealthStatus:
    """Liveness — service còn chạy không."""
    return HealthStatus(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        modelLoaded=True,
        modelVersion="yolov8n-cpu-v1.0",
        time=_now_iso(),
    )


async def _probe_yolo() -> DependencyHealth:
    """YOLO chạy in-process trong ai-vision — luôn up nếu service start thành công."""
    return DependencyHealth(
        name="ai-yolo",
        status="up",
        detail="mode=inproc, model loaded at startup",
    )


def _probe_db() -> DependencyHealth:
    if db.ping():
        stats = db.stats()
        return DependencyHealth(
            name="mysql",
            status="up",
            detail=f"detections={stats['detections']}, face_matches={stats['face_matches']}",
        )
    return DependencyHealth(name="mysql", status="down", detail="ping failed")


@app.get("/ready", response_model=ReadinessStatus, tags=["system"])
async def get_ready() -> JSONResponse:
    """Readiness — service đã sẵn sàng nhận traffic chưa.

    Compose dùng endpoint này (readiness check) để biết khi nào route traffic.
    Một dependency được coi là "down" thì overall là "not_ready".
    """
    deps: list[DependencyHealth] = [_probe_db(), await _probe_yolo()]
    overall_down = any(d.status == "down" for d in deps)
    overall: Literal["ready", "not_ready"] = "not_ready" if overall_down else "ready"
    body = ReadinessStatus(
        status=overall,
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        dependencies=deps,
        time=_now_iso(),
    )
    return JSONResponse(
        status_code=200 if overall == "ready" else 503,
        content=body.model_dump(mode="json"),
    )


@app.post("/vision/detect", response_model=DetectResponse, tags=["detection"])
async def detect_objects(req: DetectRequest, request: Request) -> JSONResponse:
    _require_auth(request)

    # OpenAPI contract: image_url XOR image_base64 (mutually exclusive).
    if not (bool(req.image_url) ^ bool(req.image_base64)):
        raise HTTPException(
            status_code=422,
            detail="Phải cung cấp image_url HOẶC image_base64 (mutually exclusive)",
        )

    started = time.perf_counter()

    # YOLO adapter: nếu input sai / YOLO không khả dụng, raise HTTPException
    # thay vì fallback stub (lỗi phải truyền ra cho client, không được ngầm bịa).
    try:
        result = yolo_adapter.run_detection(
            image_b64=req.image_base64,
            image_url=req.image_url,
            confidence_threshold=req.confidence_threshold,
        )
    except httpx.HTTPStatusError as exc:
        # YOLO service trả 4xx (input sai) hoặc 5xx (lỗi nội bộ).
        # Giữ nguyên status_code để client biết là lỗi input hay lỗi hạ tầng.
        status_code = exc.response.status_code if exc.response is not None else 502
        try:
            err_body = exc.response.json() if exc.response is not None else {}
            err_detail = err_body.get("detail", str(exc))
        except Exception:  # noqa: BLE001
            err_detail = str(exc)
        raise HTTPException(status_code=status_code, detail=f"YOLO error: {err_detail}") from exc
    except httpx.HTTPError as exc:
        # Network / timeout đến container ai-yolo — fail-fast 502.
        raise HTTPException(
            status_code=502,
            detail=f"ai-yolo không khả dụng: {exc}",
        ) from exc

    detections = [
        Detection(
            label=d.label,
            confidence=d.confidence,
            bbox=BoundingBox(x=d.bbox_x, y=d.bbox_y, width=d.bbox_w, height=d.bbox_h),
            class_id=d.class_id,
        )
        for d in result.detections
    ]

    processing_ms = int((time.perf_counter() - started) * 1000) + result.inference_time_ms
    detection_id = str(uuid.uuid4())

    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"
    if len(detections) == 0:
        risk_level = "LOW"
    elif len(detections) >= 5:
        risk_level = "HIGH"
    elif len(detections) >= 2:
        risk_level = "MEDIUM"

    response = DetectResponse(
        detection_id=detection_id,
        camera_id=req.camera_id,
        detections=detections,
        risk_level=risk_level,
        model_version=result.model_version,
        processing_time_ms=processing_ms,
        timestamp=_now_iso(),
    )

    # Lưu vào MySQL
    try:
        db.insert_detection(
            detection_id=detection_id,
            camera_id=req.camera_id,
            detections_json=json.dumps([d.model_dump() for d in detections]),
            risk_level=risk_level,
            model_version=result.model_version,
            processing_time_ms=processing_ms,
            timestamp=db.to_mysql_datetime(response.timestamp),
        )
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to save detection to MySQL: %s", exc)
        # Không fail request — detection vẫn trả về cho client

    headers = {
        "X-Detection-Id": detection_id,
        "X-Processing-Time-Ms": str(processing_ms),
        "X-Yolo-Mode": result.mode,
    }
    return JSONResponse(status_code=200, content=response.model_dump(mode="json"), headers=headers)


@app.get("/vision/detections/{detection_id}", response_model=DetectResponse, tags=["detection"])
async def get_detection_by_id(detection_id: str, request: Request) -> DetectResponse:
    _require_auth(request)
    try:
        uuid.UUID(detection_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="detection_id phải là UUID") from exc

    record = db.get_detection(detection_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Detection {detection_id} không tồn tại hoặc đã hết hạn",
        )
    return DetectResponse(**record)


@app.get("/vision/results/recent", response_model=DetectionPage, tags=["detection"])
async def get_recent_detections(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    camera_id: str | None = Query(None, pattern=r"^[a-z0-9-]+$"),
) -> DetectionPage:
    _require_auth(request)
    items, next_cursor, has_more = db.list_recent_detections(limit=limit, camera_id=camera_id)
    return DetectionPage(
        items=[DetectResponse(**item) for item in items],
        nextCursor=next_cursor,
        hasMore=has_more,
    )


@app.post("/vision/face-match", response_model=FaceMatchResponse, tags=["face-match"])
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
    await asyncio.sleep(0)  # yield

    try:
        result = face_adapter.run_face_match(
            image_b64=req.image_base64,
            image_url=req.image_url,
            reference_image_b64=req.reference_image_base64,
            reference_image_url=req.reference_image_url,
            threshold=req.threshold,
        )
    except ValueError as exc:
        # base64 / URL sai định dạng — lỗi client, trả RFC 7807 Problem+JSON 400.
        LOGGER.warning("face-match client error: %s", exc)
        return JSONResponse(
            status_code=400,
            content=_problem_400(
                instance="/vision/face-match",
                detail=str(exc),
                field="image_base64" if req.image_base64 else "image_url",
                code="INVALID_INPUT",
                message=str(exc),
            ),
            headers={"X-Trace-Id": req.trace_id or ""},
        )
    except RuntimeError as exc:
        # URL fetch upstream fail — contract quy định 400 (input sai),
        # không phải 502 (không nằm trong enum response của face-match).
        LOGGER.warning("face-match upstream fail → 400: %s", exc)
        field_name = (
            "reference_image_url"
            if "reference" in str(exc).lower()
            else "image_url"
        )
        return JSONResponse(
            status_code=400,
            content=_problem_400(
                instance="/vision/face-match",
                detail=str(exc),
                field=field_name,
                code="URL_FETCH_FAILED",
                message=str(exc),
            ),
            headers={"X-Trace-Id": req.trace_id or ""},
        )

    processing_ms = int((time.perf_counter() - started) * 1000) + result.inference_time_ms

    response = FaceMatchResponse(
        match_id=str(uuid.uuid4()),
        matched=result.matched,
        confidence=result.confidence,
        threshold=req.threshold,
        status=result.status,
        message=result.message,
        model_version=result.model_version,
        processing_time_ms=processing_ms,
        trace_id=req.trace_id,
        timestamp=_now_iso(),
    )

    # Lưu vào MySQL
    try:
        db.insert_face_match(
            match_id=response.match_id,
            matched=response.matched,
            confidence=response.confidence,
            threshold=response.threshold,
            status=response.status,
            message=response.message,
            model_version=response.model_version,
            processing_time_ms=response.processing_time_ms,
            trace_id=response.trace_id,
            timestamp=db.to_mysql_datetime(response.timestamp),
        )
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to save face match to MySQL: %s", exc)

    headers = {"X-Trace-Id": req.trace_id or ""}
    return JSONResponse(
        status_code=200,
        content=response.model_dump(mode="json"),
        headers=headers,
    )


@app.get("/vision/models/info", response_model=ModelInfo, tags=["model"])
async def get_model_info(request: Request) -> ModelInfo:
    _require_auth(request)
    return ModelInfo(
        model_id="yolov8n-cpu-v1.0",
        model_type="object_detection",
        framework="ultralytics",
        framework_version="8.3.0",
        classes=[
            {"id": 0, "name": "person", "description": "Con người"},
            {"id": 2, "name": "car", "description": "Ô tô"},
            {"id": 3, "name": "motorcycle", "description": "Xe máy"},
            {"id": 7, "name": "truck", "description": "Xe tải"},
            {"id": 15, "name": "cat", "description": "Mèo"},
            {"id": 16, "name": "dog", "description": "Chó"},
            {"id": 24, "name": "backpack", "description": "Ba lô"},
            {"id": 26, "name": "handbag", "description": "Túi xách"},
        ],
        confidence_threshold_default=0.5,
        input_size=640,
        accuracy_map=0.73,
        inference_time_ms_avg=35,
        last_updated="2026-07-15T00:00:00Z",
        status="ACTIVE",
    )