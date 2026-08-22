"""Smart Campus API Gateway.

Reverse-proxy có chọn lọc: chỉ lộ một tập endpoint curated từ 3 service
(ai-vision, core-business-mock, camera-stream-mock). 3 service chạy trong
mạng nội bộ Docker, không publish port ra host. Client chỉ giao tiếp với
Gateway qua cổng 8080.
"""
