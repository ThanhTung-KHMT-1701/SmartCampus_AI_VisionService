"""Bearer token authentication cho Gateway.

Gateway dùng token riêng (`GATEWAY_AUTH_TOKEN`) để xác thực client bên ngoài.
Token của từng service hạ lưu được giữ bí mật phía Gateway và tự động gắn vào
request khi chuyển tiếp — client không bao giờ thấy các token này.

Đây là pattern "gateway-fronted auth" đơn giản cho môi trường lab; production
có thể thay bằng JWT thật, OAuth2, hoặc mTLS giữa Gateway và từng service.
"""
from __future__ import annotations

import os

from fastapi import HTTPException, Request, status

GATEWAY_TOKEN_ENV = "GATEWAY_AUTH_TOKEN"
DEFAULT_GATEWAY_TOKEN = "local-dev-token-gateway"


def _expected_gateway_token() -> str:
    return os.environ.get(GATEWAY_TOKEN_ENV, DEFAULT_GATEWAY_TOKEN)


def require_gateway_token(request: Request) -> None:
    """Kiểm tra Bearer token của client khi gọi Gateway.

    Public endpoint (vd. `GET /health` của Gateway) không gọi hàm này.
    """
    expected = _expected_gateway_token()
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gateway: thiếu Bearer token",
        )
    token = auth[len("Bearer ") :].strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gateway: token không hợp lệ",
        )


def service_token(env_name: str, default: str) -> str:
    """Lấy token nội bộ để gọi xuống service hạ lưu.

    Token này chỉ nằm trong biến môi trường của Gateway, do compose inject từ
    `.env` (đã được `.gitignore` chặn). Không bao giờ truyền cho client.
    """
    return os.environ.get(env_name, default)
