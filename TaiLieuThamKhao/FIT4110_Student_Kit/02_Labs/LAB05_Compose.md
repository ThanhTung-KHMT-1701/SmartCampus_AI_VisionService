# Lab 05 — Docker Compose

**Purpose:** run the API together with the dependencies that its service boundary actually needs.

Use [FIT4110_lab05_docker_compose](https://github.com/TrangLe1912/FIT4110_lab05_docker_compose) as the technical starter. It is a skeleton to complete, not a finished integrated system. AI and PostgreSQL are examples; they are not mandatory when your service needs a different dependency.

## Start here

1. From the service boundary, identify the API and at least one real dependency: database, message broker, AI/worker, or another service.
2. Adapt Compose, environment variables, networks, and healthchecks; run the stack and verify that each required service is ready.
3. Prove that the API actually communicates with the dependency, run the relevant local/Newman tests, and save the evidence.

Three healthy containers alone do not prove end-to-end integration.

## If the starter does not run unchanged

Check only the items relevant to your stack:

- create the external `class-net` if the Compose file still references it;
- use healthcheck commands that exist inside each image;
- install the AI runtime dependencies and expose its port if your stack uses the sample AI service;
- connect the API to the selected dependency instead of leaving data only in memory;
- replace the TODO `test:compose` command with the real test command.

---

## Bản tiếng Việt

# Lab 05 — Docker Compose

**Mục đích:** chạy API cùng các dependency mà service boundary thực sự cần.

Dùng [FIT4110_lab05_docker_compose](https://github.com/TrangLe1912/FIT4110_lab05_docker_compose) làm technical starter. Đây là skeleton cần hoàn thiện, không phải hệ thống tích hợp sẵn. AI và PostgreSQL chỉ là ví dụ; không bắt buộc nếu service cần dependency khác.

## Bắt đầu từ đây

1. Dựa vào service boundary, xác định API và ít nhất một dependency thật: database, message broker, AI/worker hoặc service khác.
2. Điều chỉnh Compose, environment variable, network và healthcheck; chạy stack và kiểm tra từng service bắt buộc đã sẵn sàng.
3. Chứng minh API thực sự giao tiếp với dependency, chạy test local/Newman phù hợp và lưu minh chứng.

Chỉ có ba container healthy chưa chứng minh tích hợp end-to-end.

## Khi starter không chạy nguyên trạng

Chỉ kiểm tra các mục liên quan đến stack của nhóm:

- tạo external `class-net` nếu Compose file vẫn tham chiếu network này;
- dùng lệnh healthcheck có sẵn bên trong từng image;
- cài runtime dependency và mở port AI nếu stack dùng sample AI service;
- kết nối API với dependency đã chọn thay vì chỉ lưu dữ liệu trong bộ nhớ;
- thay lệnh `test:compose` còn là TODO bằng lệnh test thực tế.
