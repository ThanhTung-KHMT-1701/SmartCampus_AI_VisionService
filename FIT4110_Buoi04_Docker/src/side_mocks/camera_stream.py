"""Camera Stream mock — phục vụ consumer-side smoke test cho team-vision.

Endpoints tối thiểu (không đầy đủ contract của team-camera, chỉ đủ để verify
nhánh upstream mà AI Vision có thể phụ thuộc):

- GET  /health
- POST /frames         : frame mới từ camera
- GET  /cameras/{id}/frames/latest : lấy frame gần nhất
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Camera Stream Mock", version="0.1.0")

AUTH_TOKEN_ENV = "CAMERA_AUTH_TOKEN"
DEFAULT_TOKEN = "lab-token-camera"

_FRAMES: dict[str, dict[str, Any]] = {}
_BY_CAMERA: dict[str, list[str]] = {}


_BASE_CONFIG = ConfigDict(extra="forbid")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_auth(request: Request) -> None:
    """Chấp nhận mọi Bearer token không rỗng — đây là mock cho smoke test,
    không enforce auth thật (auth thật do service thật của team đó xử lý)."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or len(auth[len("Bearer ") :].strip()) == 0:
        raise HTTPException(status_code=401, detail="Camera: missing token")


class FrameIngestRequest(BaseModel):
    model_config = _BASE_CONFIG

    camera_id: str = Field(..., min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    frame_url: str | None = None
    motion_detected: bool = False
    timestamp: str


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "camera-stream-mock", "time": _now()}


@app.post("/frames", status_code=201)
async def ingest_frame(req: FrameIngestRequest, request: Request) -> dict[str, Any]:
    _require_auth(request)
    frame_id = str(uuid.uuid4())
    record = {
        "frame_id": frame_id,
        "camera_id": req.camera_id,
        "frame_url": req.frame_url,
        "motion_detected": req.motion_detected,
        "timestamp": req.timestamp,
    }
    _FRAMES[frame_id] = record
    _BY_CAMERA.setdefault(req.camera_id, []).append(frame_id)
    return {"frame_id": frame_id, "accepted": True}


@app.get("/cameras/{camera_id}/frames/latest")
async def latest_frame(camera_id: str, request: Request) -> dict[str, Any]:
    _require_auth(request)
    ids = _BY_CAMERA.get(camera_id, [])
    if not ids:
        raise HTTPException(status_code=404, detail="No frame for camera")
    return _FRAMES[ids[-1]]
