# API Versioning Policy

## Chính sách versioning cho AI Vision Service API

---

## 1. Nguyên tắc chung

AI Vision Service tuân thủ **Semantic Versioning (SemVer)** với format `MAJOR.MINOR.PATCH`:

- **MAJOR** (ví dụ: `2.0.0`): Thay đổi không tương thích ngược (breaking changes)
- **MINOR** (ví dụ: `1.1.0`): Thêm tính năng mới nhưng tương thích ngược
- **PATCH** (ví dụ: `1.0.1`): Sửa lỗi, không thay đổi API

---

## 2. Phiên bản hiện tại

| Phiên bản | Ngày release | Mô tả | Trạng thái |
|---|---|---|---|
| 1.0.0 | 2026-08-11 | API contract đầu tiên cho Smart Campus | **Current** |

---

## 3. Breaking Changes (MAJOR bump)

Các thay đổi sau được coi là breaking changes và sẽ bump MAJOR version:

- **Xóa endpoint** hoặc thay đổi HTTP method của endpoint
- **Thay đổi path** của endpoint (VD: `/vision/detect` → `/api/v2/detect`)
- **Thay đổi required field** trong request schema
- **Thay đổi kiểu dữ liệu** của field (VD: `string` → `integer`)
- **Xóa field** khỏi response schema
- **Thay đổi enum values** (xóa giá trị, đổi tên)
- **Thay đổi HTTP status code** của response
- **Thay đổi semantic meaning** của field

---

## 4. Non-breaking Changes (MINOR bump)

Các thay đổi sau không phải là breaking changes và chỉ cần bump MINOR version:

- **Thêm endpoint mới**
- **Thêm optional field** vào request schema
- **Thêm field mới** vào response schema ( Consumer nên bỏ qua unknown fields)
- **Thêm giá trị mới** vào enum
- **Thêm query parameter mới** (optional)
- **Mở rộng mô tả/documentation** mà không thay đổi behavior
- **Thay đổi thứ tự fields** trong response
- **Thay đổi format của error messages** (miễn là vẫn tuân thủ Problem Details)

---

## 5. Patch Changes (PATCH bump)

Các thay đổi sau chỉ cần bump PATCH version:

- **Sửa lỗi typo** trong mô tả/error messages
- **Cập nhật examples** cho chính xác hơn
- **Sửa validation rules** (VD: tăng `maxLength`)

---

## 6. URL Versioning Strategy

AI Vision Service sử dụng **URL Path Versioning**:

```
https://api.campus.local/v1/vision/detect
https://api.campus.local/v2/vision/detect
```

### Header `Accept`

Client có thể specify version qua header:

```http
GET /vision/detect HTTP/1.1
Host: ai-vision.campus.local
Accept: application/vnd.smart-campus.v1+json
```

---

## 7. Deprecation Policy

Khi deprecated một endpoint/field:

1. **Announce**: Thông báo trong `deprecation` field trong response headers
2. **Sunset Date**: Cho biết ngày endpoint sẽ bị xóa
3. **Migration Guide**: Cung cấp hướng dẫn migrate

```http
GET /v1/vision/detect HTTP/1.1

HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: <https://api.campus.local/v2/vision/detect>; rel="successor-version"
```

---

## 8. Changelog

### v1.0.0 (2026-08-11) - Initial Release

**Endpoints:**
- `GET /health` - Health check
- `POST /vision/detect` - Object detection
- `GET /vision/detections/{detectionId}` - Get detection by ID
- `GET /vision/results/recent` - Get recent detections with filtering
- `POST /vision/face-match` - Face matching
- `GET /vision/models/info` - Get AI model information

**Features:**
- Support both `image_url` and `image_base64` for image input
- Confidence threshold customization
- Cursor-based pagination for recent results
- Filter by `camera_id`, `from_time`, `to_time`
- Trace ID support for distributed tracing
- Comprehensive error responses with Problem Details

**Known Limitations:**
- No idempotency support
- Detection results cached only 24 hours
- Max image size: 10MB
- No multipart/form-data support (JSON only)

---

## 9. Migration Guide

### Migration từ v1.0.0 sang v1.1.0 (khi có)

Sẽ được cập nhật khi có breaking changes.

### Migration từ v1.x.x sang v2.0.0 (khi có)

Sẽ được cung cấp khi có breaking changes. Kế hoạch:
1. v2.0.0 sẽ được release song song với v1.0.0
2. v1.0.0 sẽ được deprecated với sunset date 6 tháng
3. Documentation và migration guide sẽ được cung cấp

---

## 10. Support Matrix

| Version | Release Date | End of Support | Notes |
|---|---|---|---|
| 1.0.0 | 2026-08-11 | TBD | Current stable |

---

## 11. Contact

Cho câu hỏi về versioning hoặc API:

- **Team**: AI Vision Service (A4)
- **Email**: ai-vision@smart-campus.edu.vn
- **Slack**: #ai-vision-support

---

## 12. References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [RFC 9110 - HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [Problem Details for HTTP APIs - RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)
