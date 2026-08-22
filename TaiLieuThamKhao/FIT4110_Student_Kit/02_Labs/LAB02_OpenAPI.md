# Lab 02 — Contract-first

**Purpose:** turn the Lab 01 service boundary into a negotiated technical contract before implementation.

Use [FIT4110_lab02_openapi](https://github.com/TrangLe1912/FIT4110_lab02_openapi) as the authoritative guide. Read the pairing matrix and assigned user story first:

- REST synchronous pairs 01, 02, 03, and 10 follow the OpenAPI 3.1, Spectral, Prism, and `curl` path.
- Queue asynchronous pairs 04–09 create the preliminary event contract specified by the source rubric; they are not forced into REST and do not need a full AsyncAPI specification in this lab.

Provider and consumer analyse independently, negotiate at least six issues, and complete the exact artefacts/checklist for their pair type in the source repository. Lab 02 uses `curl`, not Postman. Use this Kit only for the [single-repository submission workflow](../03_Guides/Submission.md).

---

## Bản tiếng Việt

# Lab 02 — Thiết kế contract-first

**Mục đích:** chuyển service boundary của Lab 01 thành hợp đồng kỹ thuật được đàm phán trước khi triển khai.

Dùng [FIT4110_lab02_openapi](https://github.com/TrangLe1912/FIT4110_lab02_openapi) làm hướng dẫn chính thức. Đọc pairing matrix và đúng user story được giao trước khi làm:

- Các cặp REST đồng bộ 01, 02, 03 và 10 làm theo nhánh OpenAPI 3.1, Spectral, Prism và `curl`.
- Các cặp Queue bất đồng bộ 04–09 tạo event contract sơ bộ theo rubric nguồn; không ép thiết kế thành REST và chưa phải viết đặc tả AsyncAPI đầy đủ trong lab này.

Provider và consumer phân tích độc lập, đàm phán ít nhất sáu vấn đề và hoàn thành đúng artefact/checklist dành cho loại cặp của mình trong repo gốc. Lab 02 dùng `curl`, chưa dùng Postman. Chỉ dùng Student Kit cho [quy trình nộp một repository duy nhất](../03_Guides/Submission.md).
