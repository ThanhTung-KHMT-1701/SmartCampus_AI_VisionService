# Docker guide

Docker packages the application with its runtime dependencies. A strong lab image is small enough to use, reproducible from its Dockerfile, configurable through environment variables, and observable through a health endpoint.

```bash
docker build -t fit4110/<service>:lab04 .
docker run --rm --name fit4110-service -p 8000:8000 --env-file .env.example fit4110/<service>:lab04
curl http://localhost:8000/health
docker logs fit4110-service
```

For Compose: `docker compose up -d --build`, `docker compose ps`, and `docker compose logs -f`. Stop only your stack with `docker compose down`. `docker compose down -v` also removes that stack’s volumes; use it only when you intend to discard its data.

## Bản dịch tiếng Việt

Docker đóng gói ứng dụng cùng dependency runtime. Image phải tái lập được, có cấu hình qua environment, health endpoint và log rõ. Với Compose, chạy build/up, kiểm tra ps/logs; `down -v` xoá volume nên chỉ dùng khi muốn xoá dữ liệu.
