# Checklist - Buổi 02 OpenAPI Contract

## Yêu cầu bắt buộc

| # | Tiêu chí | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | `openapi.yaml` dùng **OpenAPI 3.1.0** | ✅ Pass | Spectral verified |
| 2 | Có tối thiểu 4 path phù hợp user story | ✅ Pass | 6 endpoints total |
| 3 | Schema trong `components/schemas` dùng `$ref` | ✅ Pass | All schemas in components |
| 4 | Có ít nhất một ví dụ `oneOf` + `discriminator` hoặc `anyOf` | ✅ Pass | DetectRequest uses anyOf |
| 5 | Union type với `null` | ✅ Pass | Multiple fields use `type: [string, 'null']` |
| 6 | Response lỗi dùng `Problem Details` | ✅ Pass | All error responses use Problem schema |
| 7 | File pass `spectral lint` | ✅ Pass | No errors |
| 8 | `negotiation-log.md` có tối thiểu 6 issues | ✅ Pass | 8 issues documented |

---

## Chi tiết Spectral Validation

```
spectral lint openapi.yaml --ruleset campus-spectral.yaml
```

**Kết quả**: No results with a severity of 'error' found!

---

## Chi tiết Endpoints

### Pair 01: Camera Stream → AI Vision

| Endpoint | Method | Path | Schema | Example |
|---|---|---|---|---|
| Health | GET | `/health` | HealthStatus | ✅ |
| Detect Objects | POST | `/vision/detect` | DetectRequest, DetectResponse | ✅ |
| Get Detection | GET | `/vision/detections/{detectionId}` | DetectResponse | ✅ |
| Model Info | GET | `/vision/models/info` | ModelInfo | ✅ |

### Pair 02: Core Business → AI Vision

| Endpoint | Method | Path | Schema | Example |
|---|---|---|---|---|
| Face Match | POST | `/vision/face-match` | FaceMatchRequest, FaceMatchResponse | ✅ |
| Recent Results | GET | `/vision/results/recent` | DetectionPage | ✅ |

---

## Error Responses Coverage

| Status Code | Response | Problem Schema | Notes |
|---|---|---|---|
| 400 | BadRequest | ✅ | Validation errors |
| 401 | Unauthorized | ✅ | Missing/invalid auth |
| 404 | NotFound | ✅ | Resource not found |
| 408 | RequestTimeout | ✅ | Processing timeout |
| 413 | PayloadTooLarge | ✅ | Image too large |
| 422 | UnprocessableEntity | ✅ | Business rule violation |
| 500 | InternalServerError | ✅ | Server error |
| 503 | ServiceUnavailable | ✅ | Service down |

---

## Files bàn giao

| File | Mô tả | Hoàn thành |
|---|---|---|
| `openapi.yaml` | Hợp đồng API hoàn chỉnh | ✅ |
| `docs/analysis-provider.md` | Phân tích Provider | ✅ |
| `docs/analysis-consumer.md` | Phân tích Consumer | ✅ |
| `negotiation-log.md` | Biên bản đàm phán | ✅ |
| `VERSIONING.md` | Chính sách versioning | ✅ |
| `evidence/buoi-02/spectral-report.txt` | Spectral lint report | ✅ |
| `evidence/buoi-02/README.md` | Evidence summary | ✅ |

---

## Sign-off

- [x] Provider: AI Vision Team (A4)
- [x] Consumer: Camera Stream Team (A2) - Pair 01
- [x] Consumer: Core Business Team (A6) - Pair 02
- [ ] Witness (GV/TA): _____________________

Date: 2026-08-11
