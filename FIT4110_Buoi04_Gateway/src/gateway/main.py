"""FastAPI app — Smart Campus API Gateway.

Khởi tạo app, lifespan (đóng httpx client khi shutdown), các endpoint curated,
và health endpoint tổng hợp từ 3 service hạ lưu.
"""
from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from .auth import require_gateway_token, service_token
from .proxy import (
    AI_VISION_BASE,
    CAMERA_STREAM_BASE,
    CORE_BUSINESS_BASE,
    close_client,
    forward,
    get_client,
)
from .routes import ROUTE_TABLE, RouteSpec


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_client()
    try:
        yield
    finally:
        await close_client()


app = FastAPI(
    title="Smart Campus API Gateway",
    version="1.0.0",
    description=(
        "API Gateway có chọn lọc cho 3 service hạ lưu (ai-vision, "
        "core-business-mock, camera-stream-mock). 3 service chạy nội bộ, "
        "không publish port; client chỉ giao tiếp qua Gateway."
    ),
    lifespan=lifespan,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@app.get("/health", tags=["health"])
async def gateway_health() -> dict[str, Any]:
    """Health của chính Gateway — không cần auth."""
    return {
        "status": "ok",
        "service": "api-gateway",
        "version": "1.0.0",
        "upstreams": {
            "ai-vision": AI_VISION_BASE,
            "core-business-mock": CORE_BUSINESS_BASE,
            "camera-stream-mock": CAMERA_STREAM_BASE,
        },
        "routesExposed": [r.gateway_path for r in ROUTE_TABLE],
        "time": _now_iso(),
    }


@app.get("/health/services", tags=["health"])
async def upstream_health(_request: Request) -> JSONResponse:
    """Gọi `/health` của 3 service song song — aggregate kết quả.

    Không yêu cầu Bearer token (chỉ trả lời "ok" / "down" — không lộ token
    hay dữ liệu nhạy cảm nào).
    """
    targets = (
        ("ai-vision", AI_VISION_BASE, "/health"),
        ("core-business-mock", CORE_BUSINESS_BASE, "/health"),
        ("camera-stream-mock", CAMERA_STREAM_BASE, "/health"),
    )

    async def _probe(name: str, base: str, path: str) -> tuple[str, dict[str, Any]]:
        started = time.perf_counter()
        try:
            resp = await forward(base, "GET", path, timeout=3.0)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return name, {
                "status": "up" if resp.status_code == 200 else "degraded",
                "httpStatus": resp.status_code,
                "latencyMs": elapsed_ms,
                "body": _safe_json(resp),
            }
        except Exception as exc:  # noqa: BLE001 — aggregate luôn cả trả về
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return name, {
                "status": "down",
                "httpStatus": None,
                "latencyMs": elapsed_ms,
                "error": type(exc).__name__,
            }

    results = await asyncio.gather(*[_probe(n, b, p) for n, b, p in targets])
    overall = "ok"
    if any(r[1]["status"] == "down" for r in results):
        overall = "down"
    elif any(r[1]["status"] != "up" for r in results):
        overall = "degraded"
    return JSONResponse(
        status_code=200 if overall == "ok" else 503,
        content={"status": overall, "time": _now_iso(), "services": dict(results)},
    )


def _safe_json(resp: Any) -> Any:
    """Cố gắng parse JSON; trả None nếu body không phải JSON."""
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return None


def _filtered_upstream_headers(headers: Any, *, drop: set[str]) -> dict[str, str]:
    """Loại bỏ header nhạy cảm (vd. `content-length` từ upstream) khi relay.

    `hop-by-hop` headers theo RFC 7230 cũng nên loại bỏ; ở mức lab ta chỉ lọc
    một số header hay gây xung đột.
    """
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in drop:
            continue
        if lk.startswith("x-internal-") or lk.startswith("internal-"):
            continue
        out[k] = v
    return out


HOP_BY_HOP = {
    "content-length",
    "transfer-encoding",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "upgrade",
    "host",
    "server",
    "date",
}


async def _handle_route(spec: RouteSpec, request: Request, **path_params: Any) -> JSONResponse:
    """Xử lý chung cho mọi route trong `ROUTE_TABLE`.

    - Yêu cầu Bearer Gateway token (gọi `require_gateway_token`).
    - Chuyển tiếp Authorization mang token nội bộ của service đó.
    - Forward headers còn lại (đã loại hop-by-hop).
    - Trả lại status_code, body và headers (trừ hop-by-hop) của upstream.
    """
    require_gateway_token(request)

    upstream_path = spec.upstream_path.format(**path_params)
    upstream_token = service_token(spec.upstream_token_env, spec.upstream_token_default)

    fwd_headers = {
        "Authorization": f"Bearer {upstream_token}",
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "Accept": request.headers.get("Accept", "application/json"),
        "User-Agent": "smartcampus-gateway/1.0",
    }

    body: Any = None
    if spec.method in {"POST", "PUT", "PATCH"}:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(  # noqa: B904
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Body phải là JSON hợp lệ",
            )

    try:
        # Tránh truyền `json_body=None` cho GET (sẽ ép httpx serialize None → b'null').
        kwargs: dict[str, Any] = {
            "headers": fwd_headers,
        }
        if spec.method.upper() != "GET":
            kwargs["json_body"] = body
        upstream_resp = await forward(
            spec.upstream_base,
            spec.method,
            upstream_path,
            **kwargs,
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "type": "https://gateway.campus.local/errors/upstream",
                "title": "Upstream không phản hồi",
                "status": 502,
                "detail": f"Không liên lạc được với {spec.upstream_base}",
                "upstreamError": type(exc).__name__,
            },
            media_type="application/problem+json",
        )

    response_headers = _filtered_upstream_headers(
        upstream_resp.headers, drop=HOP_BY_HOP
    )
    return JSONResponse(
        status_code=upstream_resp.status_code,
        content=_safe_json(upstream_resp),
        headers=response_headers,
    )


def register_routes() -> None:
    """Đăng ký các route từ `ROUTE_TABLE` lên FastAPI app.

    Dùng `add_api_route` thay vì decorator để bảng route là nguồn dữ liệu duy
    nhất — thêm/bớt route chỉ cần sửa `routes.py`.

    Lưu ý: KHÔNG dùng `*args`/`**kwargs` trong handler — FastAPI sẽ coi đó là
    query-string và validate. Path params được lấy trực tiếp từ
    `request.path_params` (đã được FastAPI populate sẵn cho mọi route).
    """
    def _make_handler(spec: RouteSpec):
        async def handler(request: Request) -> JSONResponse:
            return await _handle_route(spec, request, **request.path_params)
        return handler

    for spec in ROUTE_TABLE:
        endpoint = _make_handler(spec)
        app.add_api_route(
            spec.gateway_path,
            endpoint,
            methods=[spec.method],
            summary=spec.summary,
            tags=["proxied"],
        )


register_routes()


@app.get("/routes", tags=["meta"])
async def list_routes() -> dict[str, Any]:
    """Liệt kê các route mà Gateway lộ (debug/dashboard)."""
    return {
        "gatewayHealth": "/health",
        "upstreamHealth": "/health/services",
        "routes": [
            {
                "method": r.method,
                "path": r.gateway_path,
                "upstream": r.upstream_base + r.upstream_path,
                "auth": "Bearer GATEWAY_TOKEN",
            }
            for r in ROUTE_TABLE
        ],
        "time": _now_iso(),
    }
