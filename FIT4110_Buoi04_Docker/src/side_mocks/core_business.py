"""Core Business mock — phục vụ consumer-side smoke test cho team-vision.

Endpoints tối thiểu:

- GET  /health
- GET  /alerts/recent   : danh sách alert gần đây
- POST /policies/evaluate-detection : tạo alert nếu detection có rủi ro cao
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Core Business Mock", version="0.1.0")

AUTH_TOKEN_ENV = "CORE_AUTH_TOKEN"
DEFAULT_TOKEN = "lab-token-core"

_ALERTS: dict[str, dict[str, Any]] = {}
_ORDER: list[str] = []


_BASE_CONFIG = ConfigDict(extra="forbid")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_auth(request: Request) -> None:
    """Chấp nhận mọi Bearer token không rỗng — mock cho smoke test."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or len(auth[len("Bearer ") :].strip()) == 0:
        raise HTTPException(status_code=401, detail="Core: missing token")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "core-business-mock", "time": _now()}


@app.get("/alerts/recent")
async def alerts_recent(
    request: Request,
    limit: int = 20,
) -> dict[str, Any]:
    _require_auth(request)
    items = list(reversed(_ORDER))[:limit]
    has_more = len(_ORDER) > limit
    return {
        "items": [_ALERTS[i] for i in items],
        "nextCursor": None,
        "hasMore": has_more,
    }


class EvaluateDetectionRequest(BaseModel):
    model_config = _BASE_CONFIG

    detection_id: str
    camera_id: str = Field(..., min_length=1, max_length=80)
    risk_level: str = Field(..., pattern=r"^(LOW|MEDIUM|HIGH|CRITICAL)$")
    timestamp: str


@app.post("/policies/evaluate-detection", status_code=200)
async def evaluate_detection(req: EvaluateDetectionRequest, request: Request) -> dict[str, Any]:
    _require_auth(request)
    alert_id = str(uuid.uuid4())
    severity_map = {"LOW": "info", "MEDIUM": "warning", "HIGH": "high", "CRITICAL": "critical"}
    severity = severity_map.get(req.risk_level, "info")
    record = {
        "alert_id": alert_id,
        "detection_id": req.detection_id,
        "camera_id": req.camera_id,
        "severity": severity,
        "risk_level": req.risk_level,
        "status": "OPEN",
        "created_at": _now(),
    }
    _ALERTS[alert_id] = record
    _ORDER.append(alert_id)
    return record
