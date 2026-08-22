"""Định tuyến curated: Gateway chỉ lộ một số route nhất định.

Mỗi route là một tuple `(method, path, target_service, target_path)` để dễ
đọc, dễ mở rộng. Khi muốn thêm/bớt endpoint, chỉ cần sửa bảng ROUTE_TABLE ở
đây, không phải đụng vào `main.py`.
"""
from __future__ import annotations

from dataclasses import dataclass

from .proxy import AI_VISION_BASE, CAMERA_STREAM_BASE, CORE_BUSINESS_BASE


@dataclass(frozen=True)
class RouteSpec:
    method: str
    gateway_path: str
    upstream_base: str
    upstream_path: str
    upstream_token_env: str
    upstream_token_default: str
    summary: str


ROUTE_TABLE: tuple[RouteSpec, ...] = (
    RouteSpec(
        method="POST",
        gateway_path="/api/vision/detect",
        upstream_base=AI_VISION_BASE,
        upstream_path="/vision/detect",
        upstream_token_env="AI_VISION_AUTH_TOKEN",
        upstream_token_default="local-dev-token-vision",
        summary="Object detection (chuyển tiếp tới AI Vision Service).",
    ),
    RouteSpec(
        method="POST",
        gateway_path="/api/policies/evaluate-detection",
        upstream_base=CORE_BUSINESS_BASE,
        upstream_path="/policies/evaluate-detection",
        upstream_token_env="CORE_AUTH_TOKEN",
        upstream_token_default="lab-token-core",
        summary="Đánh giá chính sách cho một detection (Core Business).",
    ),
    RouteSpec(
        method="GET",
        gateway_path="/api/cameras/{camera_id}/frames/latest",
        upstream_base=CAMERA_STREAM_BASE,
        upstream_path="/cameras/{camera_id}/frames/latest",
        upstream_token_env="CAMERA_AUTH_TOKEN",
        upstream_token_default="lab-token-camera",
        summary="Lấy frame mới nhất theo camera (Camera Stream).",
    ),
)
