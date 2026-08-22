# Learning map

| Phase | Question answered | Main artefact |
|---|---|---|
| Preparation | Can I run the toolchain? | setup evidence |
| Service Boundary | What does my service own? | boundary document |
| Contract | What promise do provider and consumer share? | `openapi.yaml` or event contract |
| Testing | Does the REST promise hold in expected and bad cases? | Postman + Newman report, where applicable |
| Docker | Does the service run consistently anywhere? | Dockerfile + image evidence |
| Compose | Can the dependencies run together? | `docker-compose.yml` |
| Integration / Plug-a-thon | Can independent teams connect safely? | handshake + demo |
| Final Demo | Can another person reproduce and understand it? | demo pack |

The hand-off is intentional: each lab consumes the verified artefacts of the previous one. Keep filenames predictable and do not discard earlier evidence.

---

# Bản dịch tiếng Việt

| Giai đoạn | Câu hỏi cần trả lời | Artefact chính |
|---|---|---|
| Chuẩn bị | Tôi chạy được toolchain chưa? | minh chứng môi trường |
| Ranh giới service | Service của tôi sở hữu điều gì? | tài liệu boundary |
| Contract | Provider và consumer cùng cam kết điều gì? | `openapi.yaml` hoặc event contract |
| Kiểm thử | Cam kết REST có đúng với dữ liệu hợp lệ và lỗi? | Postman + Newman report, khi phù hợp |
| Docker | Service có chạy nhất quán ở nơi khác không? | Dockerfile + minh chứng image |
| Compose | Các phụ thuộc có chạy cùng nhau không? | `docker-compose.yml` |
| Tích hợp / Plug-a-thon | Các nhóm độc lập có kết nối an toàn không? | handshake + demo |
| Final Demo | Người khác có chạy lại và hiểu được không? | demo pack |

Việc bàn giao giữa các Lab là có chủ đích: mỗi Lab dùng artefact đã được kiểm chứng từ Lab trước. Giữ tên file nhất quán và không xoá minh chứng cũ.
