# Lab 03 — Postman, mocks, and contract tests

**Purpose:** turn the agreed contract into executable requests, assertions, reports, and consumer/provider integration evidence.

Use [FIT4110_lab03_postman_mock_testing](https://github.com/TrangLe1912/FIT4110_lab03_postman_mock_testing) as the authoritative guide. Use one Postman collection with `mock` and `local` environments, keep URLs/tokens in environment variables, run Newman, and complete the source test matrix, handshake, reliability checklist, and required reports.

Important: Prism validates contract-shaped mock responses but does not prove real authentication. Missing-token and wrong-token evidence must be verified against the real local service; `Prefer: code=401` is not an authentication test.

This lab's executable flow is for REST APIs: OpenAPI → Prism → Postman → Newman. For Queue asynchronous pairs, continue documenting the event contract, topic, payload, correlation ID, retry, and dead-letter handling; message-broker integration testing follows the published Lab 05 or Plug-a-thon instructions.

---

## Bản tiếng Việt

# Lab 03 — Postman, mock và contract test

**Mục đích:** chuyển contract đã thống nhất thành request, assertion, report và minh chứng tích hợp provider/consumer có thể thực thi.

Dùng [FIT4110_lab03_postman_mock_testing](https://github.com/TrangLe1912/FIT4110_lab03_postman_mock_testing) làm hướng dẫn chính thức. Dùng một Postman collection với hai environment `mock` và `local`, đặt URL/token trong environment variable, chạy Newman và hoàn thành test matrix, handshake, reliability checklist cùng các report mà repo gốc yêu cầu.

Lưu ý: Prism kiểm tra mock response theo cấu trúc contract nhưng không chứng minh authentication thật. Minh chứng thiếu token và token sai phải được kiểm tra trên local service thật; `Prefer: code=401` không phải auth test.

Luồng thực thi của Lab này dành cho REST API: OpenAPI → Prism → Postman → Newman. Với các cặp Queue bất đồng bộ, tiếp tục tài liệu hóa event contract, topic, payload, correlation ID, retry và dead-letter handling; kiểm thử tích hợp message broker thực hiện theo hướng dẫn Lab 05 hoặc Plug-a-thon được công bố.
