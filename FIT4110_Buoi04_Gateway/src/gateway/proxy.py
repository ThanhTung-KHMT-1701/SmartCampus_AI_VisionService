"""HTTP proxy tới 3 service hạ lưu.

Một `httpx.AsyncClient` duy nhất, dùng connection pool, giúp gateway chịu tải
tốt hơn khi gọi liên tục. Timeout mặc định 10s cho mọi call hạ lưu; client
có thể truyền `?timeout=...` để tăng cho tác vụ nặng (khi đó timeout phải
<= 30s để tránh chiếm worker).
"""
from __future__ import annotations

import os
from typing import Any

import httpx


def _base_url(env_name: str, default: str) -> str:
    return os.environ.get(env_name, default).rstrip("/")


AI_VISION_BASE = _base_url("AI_VISION_BASE_URL", "http://ai-vision:8000")
CORE_BUSINESS_BASE = _base_url("CORE_BUSINESS_BASE_URL", "http://core-business-mock:4012")
CAMERA_STREAM_BASE = _base_url("CAMERA_STREAM_BASE_URL", "http://camera-stream-mock:4014")

DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_TIMEOUT_SECONDS = 30.0

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Lazy singleton — chỉ tạo client khi cần (lifespan hook sẽ đóng)."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT_SECONDS,
            follow_redirects=False,
        )
    return _client


async def close_client() -> None:
    """Đóng client khi Gateway shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _resolve_timeout(timeout: float | None) -> httpx.Timeout:
    if timeout is None:
        return httpx.Timeout(DEFAULT_TIMEOUT_SECONDS)
    t = max(1.0, min(float(timeout), MAX_TIMEOUT_SECONDS))
    return httpx.Timeout(t)


async def forward(
    base: str,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    timeout: float | None = None,
) -> httpx.Response:
    """Gọi xuống service hạ lưu và trả về `httpx.Response` gốc.

    Caller chịu trách nhiệm chuyển response thành `JSONResponse` của FastAPI
    sao cho status_code, headers (đặc biệt là `X-Detection-Id`...) và body
    được giữ nguyên.
    """
    url = f"{base}{path}"
    client = get_client()
    return await client.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=json_body,
        timeout=_resolve_timeout(timeout),
    )
