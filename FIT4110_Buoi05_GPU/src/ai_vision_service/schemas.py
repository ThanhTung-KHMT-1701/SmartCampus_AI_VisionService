"""Pydantic models cho AI Vision Service — schema khớp openapi.yaml."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_BASE_CONFIG = ConfigDict(extra="forbid", protected_namespaces=())


class BoundingBox(BaseModel):
    model_config = _BASE_CONFIG

    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)


class Detection(BaseModel):
    model_config = _BASE_CONFIG

    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    class_id: int | None = None


class DetectRequest(BaseModel):
    model_config = _BASE_CONFIG

    camera_id: str = Field(..., min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    image_url: str | None = None
    image_base64: str | None = None
    timestamp: str
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    model_version: str | None = None


RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class DetectResponse(BaseModel):
    model_config = _BASE_CONFIG

    detection_id: str
    camera_id: str
    detections: list[Detection]
    risk_level: RiskLevel
    model_version: str
    processing_time_ms: int = Field(..., ge=0)
    timestamp: str


class DetectionPage(BaseModel):
    model_config = _BASE_CONFIG

    items: list[DetectResponse] = Field(..., min_length=0, max_length=100)
    nextCursor: str | None = None
    hasMore: bool


class FaceMatchRequest(BaseModel):
    model_config = _BASE_CONFIG

    image_url: str | None = None
    image_base64: str | None = None
    reference_image_url: str | None = None
    reference_image_base64: str | None = None
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    trace_id: str | None = Field(default=None, max_length=100)
    timestamp: str


FaceMatchStatus = Literal["MATCHED", "NOT_MATCHED", "LOW_CONFIDENCE", "ERROR"]


class FaceMatchResponse(BaseModel):
    model_config = _BASE_CONFIG

    match_id: str
    matched: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    threshold: float = Field(..., ge=0.0, le=1.0)
    status: FaceMatchStatus
    message: str | None = Field(default=None, max_length=500)
    model_version: str
    processing_time_ms: int = Field(..., ge=0)
    trace_id: str | None = None
    timestamp: str


class ModelClass(BaseModel):
    model_config = _BASE_CONFIG

    id: int
    name: str
    description: str | None = None


ModelStatus = Literal["ACTIVE", "LOADING", "ERROR", "DEPRECATED"]


class ModelInfo(BaseModel):
    model_config = _BASE_CONFIG

    model_id: str
    model_type: Literal["object_detection", "face_recognition", "anomaly_detection"]
    framework: str
    framework_version: str
    classes: list[ModelClass]
    confidence_threshold_default: float | None = Field(default=None, ge=0.0, le=1.0)
    input_size: int
    accuracy_map: float | None = Field(default=None, ge=0.0, le=1.0)
    inference_time_ms_avg: int
    last_updated: str
    status: ModelStatus


class HealthStatus(BaseModel):
    model_config = _BASE_CONFIG

    status: Literal["ok"]
    service: str
    version: str
    modelLoaded: bool
    modelVersion: str | None = None
    time: str


class ProblemDetails(BaseModel):
    """RFC 9457 — dùng cho tất cả response lỗi."""

    model_config = _BASE_CONFIG

    type: str
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str | None = None
    instance: str | None = None
