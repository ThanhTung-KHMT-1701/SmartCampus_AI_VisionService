# FIT4110_Buoi04_Gateway — Smart Campus API Gateway

Một **API Gateway** có chọn lọc đặt trước 3 service hiện có:

| Service hạ lưu | Image | Port nội bộ | Được Gateway lộ? |
|---|---|---|---|
| ai-vision | `fit4110/ai-vision:lab04` | 8000 | Có — `POST /api/vision/detect` |
| core-business-mock | `fit4110/core-business-mock:lab04` | 4012 | Có — `POST /api/policies/evaluate-detection` |
| camera-stream-mock | `fit4110/camera-stream-mock:lab04` | 4014 | Có — `GET /api/cameras/{id}/frames/latest` |

**Đặc điểm chính:**

- 3 service hạ lưu **không publish port ra host** — chỉ giao tiếp qua mạng nội bộ `lab-net-gateway`.
- **Chỉ Gateway** publish `8080:8080` ra host — đây là surface duy nhất ra Internet.
- Client chỉ cần biết **một token Gateway**; token nội bộ của 3 service được Gateway tự động chèn khi chuyển tiếp (không bao giờ rò rỉ cho client).
- Thêm/bớt route chỉ cần sửa `src/gateway/routes.py` (bảng `ROUTE_TABLE`).
- Tương thích với các image từ `FIT4110_Buoi04_Docker` — không cần build lại.

## Cấu trúc thư mục

```
FIT4110_Buoi04_Gateway/
├── README.md
├── Dockerfile                  # Gateway image (multi-stage, non-root)
├── docker-compose.yml          # 3 downstream + gateway, gateway publishes 8080
├── .env.example
├── .dockerignore
├── requirements.txt            # fastapi + uvicorn + pydantic + httpx
├── src/gateway/
│   ├── __init__.py
│   ├── auth.py                 # xác thực Bearer Gateway
│   ├── proxy.py                # httpx.AsyncClient tới upstream
│   ├── routes.py               # bảng ROUTE_TABLE
│   └── main.py                 # FastAPI app + lifespan
└── docs/
    └── docker-evidence.md      # ghi chép thực nghiệm
```

## Chạy nhanh

```bash
# 1. Khởi động stack
docker compose up -d --build

# 2. Kiểm tra Gateway + 3 upstream
curl -s http://localhost:8080/health           | python -m json.tool
curl -s http://localhost:8080/health/services  | python -m json.tool
curl -s http://localhost:8080/routes           | python -m json.tool

# 3. Gọi 1 endpoint curated (cần Bearer GATEWAY_TOKEN)
curl -s -X POST http://localhost:8080/api/vision/detect \
  -H 'Authorization: Bearer local-dev-token-gateway' \
  -H 'Content-Type: application/json' \
  --data-binary '{"camera_id":"cam-gate-01","image_url":"http://storage.campus.local/images/frame-001.jpg","timestamp":"2026-08-22T10:00:00Z","confidence_threshold":0.6}'
```

## Bảng so sánh với `FIT4110_Buoi04_Docker`

| Khía cạnh | Lab04 (cũ) | Lab04_Gateway (mới) |
|---|---|---|
| Service lộ port host | 3 service (8000, 4012, 4014) | chỉ Gateway (8080) |
| Token client phải biết | 3 token (mỗi service một token) | 1 token (GATEWAY_TOKEN) |
| Có thể gọi endpoint nào | toàn bộ route của 3 service | bảng `ROUTE_TABLE` (curated) |
| Khi upstream tạch | request fail hoặc trả 5xx | Gateway trả 502 problem+json có `upstreamError` |
| Mở rộng route | sửa code 3 service | sửa 1 dòng trong `routes.py` |

## Bảo mật

- Tất cả biến `*_AUTH_TOKEN` chỉ đặt trong `.env` (đã được `.gitignore` chặn); file công khai là `.env.example` chỉ chứa placeholder lab.
- Gateway chạy non-root (UID `appuser` trong image runtime).
- Hop-by-hop headers (RFC 7230) được loại bỏ khi relay để tránh header smuggling.
- Pattern được mô tả chi tiết trong `docs/docker-evidence.md`.
