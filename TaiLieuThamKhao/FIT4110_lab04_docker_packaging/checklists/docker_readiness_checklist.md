# Docker Readiness Checklist

## Dockerfile

- [ ] Có base image hợp lý.
- [ ] Có `WORKDIR`.
- [ ] Có copy dependency trước source để tận dụng cache.
- [ ] Có `EXPOSE`.
- [ ] Có `CMD` hoặc `ENTRYPOINT`.
- [ ] Có `HEALTHCHECK`.
- [ ] Có user non-root.
- [ ] Không chứa secret thật.

## Runtime

- [ ] Container chạy được.
- [ ] Port map đúng.
- [ ] `/health` trả `200`.
- [ ] Log khởi động rõ ràng.
- [ ] Cấu hình qua ENV.

## Testing

- [ ] Chạy lại Postman Collection từ Lab 03.
- [ ] Newman report sinh ra trong `reports/`.
- [ ] Functional test pass.
- [ ] Auth test pass trên local/container.
- [ ] Negative test pass trên local/container.
- [ ] Boundary test pass hoặc có giải thích hợp đồng.

## Evidence

- [ ] Có ảnh/log `docker build`.
- [ ] Có ảnh/log `docker run`.
- [ ] Có ảnh/log `curl /health`.
- [ ] Có Newman HTML/XML report.
- [ ] Có tag image đúng quy ước.
