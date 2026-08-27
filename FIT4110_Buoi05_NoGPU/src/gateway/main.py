"""AI Vision Gateway Service.

Gateway này đóng vai trò:
- Duy nhất entry point ra bên ngoài (port 8000)
- Xác thực Bearer token
- Forward requests đến AI Vision Service (internal)
- Kết nối với MySQL để lưu trữ
"""
from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Import schemas từ ai_vision_service
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_vision_service.schemas import (
    DetectRequest,
    DetectResponse,
    DetectionPage,
    FaceMatchRequest,
    FaceMatchResponse,
    HealthStatus,
    ModelInfo,
    ProblemDetails,
)
from ai_vision_service.mysql_store import DetectionStore, FaceMatchStore

app = FastAPI(
    title="AI Vision Gateway",
    version="1.0.0",
    description="Smart Campus AI Vision API Gateway - Secure entry point",
)

# Environment variables
AUTH_TOKEN_ENV = "AI_VISION_AUTH_TOKEN"
DEFAULT_TOKEN = "smartcampus-vision-2026-secure-token"
AI_VISION_INTERNAL_URL = os.environ.get("AI_VISION_INTERNAL_URL", "http://ai-vision-internal:9000")

# HTTP client for internal communication
http_client = httpx.AsyncClient(timeout=60.0)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    DetectionStore.init_db()
    FaceMatchStore.init_db()


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_auth(request: Request) -> None:
    """Validate Bearer token."""
    expected = os.environ.get(AUTH_TOKEN_ENV, DEFAULT_TOKEN)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Bearer token",
        )
    token = auth[len("Bearer "):].strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
        )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return RFC 9457 Problem Details for validation errors."""
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
    """Return RFC 9457 Problem Details for HTTP exceptions."""
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
    """Health check endpoint (no auth required)."""
    return HealthStatus(
        status="ok",
        service="ai-vision-gateway",
        version="1.0.0",
        modelLoaded=True,
        modelVersion="yolov8n-v1.0",
        time=_now_iso(),
    )


@app.post("/vision/detect", response_model=DetectResponse, tags=["detection"])
async def detect_objects(req: DetectRequest, request: Request) -> JSONResponse:
    """Object detection endpoint - forward to internal AI service."""
    _require_auth(request)
    
    started = time.perf_counter()
    
    # Forward request to internal AI Vision service
    try:
        response = await http_client.post(
            f"{AI_VISION_INTERNAL_URL}/vision/detect",
            json=req.model_dump(mode="json", exclude_none=True),
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        # Forward error from internal service
        status_code = exc.response.status_code
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        raise HTTPException(status_code=status_code, detail=detail)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Internal AI service unavailable: {exc}",
        )
    
    processing_ms = int((time.perf_counter() - started) * 1000)
    
    # Parse response
    detect_response = DetectResponse(**data)
    
    # Save to database
    try:
        DetectionStore.add(detect_response)
    except Exception:
        pass  # Don't block response if DB fails
    
    headers = {
        "X-Detection-Id": detect_response.detection_id,
        "X-Processing-Time-Ms": str(processing_ms),
    }
    return JSONResponse(
        status_code=200,
        content=detect_response.model_dump(mode="json"),
        headers=headers,
    )


@app.get("/vision/detections/{detection_id}", response_model=DetectResponse, tags=["detection"])
async def get_detection_by_id(detection_id: str, request: Request) -> DetectResponse:
    """Get detection by ID from database."""
    _require_auth(request)
    
    import uuid
    try:
        uuid.UUID(detection_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="detection_id phải là UUID") from exc
    
    record = DetectionStore.get(detection_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Detection {detection_id} không tồn tại",
        )
    return record


@app.get("/vision/results/recent", response_model=DetectionPage, tags=["detection"])
async def get_recent_detections(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    camera_id: str | None = Query(None, pattern=r"^[a-z0-9-]+$"),
) -> DetectionPage:
    """List recent detections from database."""
    _require_auth(request)
    
    items, next_cursor, has_more = DetectionStore.list_recent(
        limit=limit,
        camera_id=camera_id,
    )
    return DetectionPage(
        items=items,
        nextCursor=next_cursor,
        hasMore=has_more,
    )


@app.post("/vision/face-match", response_model=FaceMatchResponse, tags=["face-match"])
async def face_match(req: FaceMatchRequest, request: Request) -> JSONResponse:
    """Face matching endpoint - forward to internal AI service."""
    _require_auth(request)
    
    started = time.perf_counter()
    
    # Forward request to internal AI Vision service
    try:
        response = await http_client.post(
            f"{AI_VISION_INTERNAL_URL}/vision/face-match",
            json=req.model_dump(mode="json", exclude_none=True),
            headers={"Authorization": request.headers.get("Authorization", "")},
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        raise HTTPException(status_code=status_code, detail=detail)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Internal AI service unavailable: {exc}",
        )
    
    processing_ms = int((time.perf_counter() - started) * 1000)
    
    # Parse response
    face_response = FaceMatchResponse(**data)
    
    # Save to database
    try:
        FaceMatchStore.add(face_response)
    except Exception:
        pass  # Don't block response if DB fails
    
    headers = {"X-Trace-Id": req.trace_id or ""}
    return JSONResponse(
        status_code=200,
        content=face_response.model_dump(mode="json"),
        headers=headers,
    )


@app.get("/vision/models/info", response_model=ModelInfo, tags=["model"])
async def get_model_info(request: Request) -> ModelInfo:
    """Get model information."""
    _require_auth(request)
    
    return ModelInfo(
        model_id="yolov8n-v1.0",
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
        ],
        confidence_threshold_default=0.5,
        input_size=640,
        accuracy_map=0.73,
        inference_time_ms_avg=35,
        last_updated="2026-07-15T00:00:00Z",
        status="ACTIVE",
    )
