# Xử lý lỗi nhanh

## Docker daemon chưa chạy
Mở Docker Desktop, đợi trạng thái Running rồi chạy `docker info`.

## Windows/WSL2
Chạy `wsl -l -v`; backend nên ở Version 2.

## Port 8081 hoặc 5000 bị chiếm
- Windows: `netstat -ano | findstr :8081`
- macOS/Linux: `lsof -i :8081`

## Apple Silicon
Image Ultralytics là phần tùy chọn. Có thể thử `--platform linux/amd64`, nhưng không dùng emulation để kết luận hiệu năng.

## Dọn Docker
`docker system prune -a` có thể xóa image không dùng. Chỉ chạy khi hiểu tác động.
