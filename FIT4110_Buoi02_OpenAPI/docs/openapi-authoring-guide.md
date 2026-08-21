# Hướng dẫn viết `openapi.yaml` cho Lab 02

## 1. Khung bắt buộc

```yaml
openapi: 3.1.0
info:
  title: Smart Campus — <Tên service>
  version: 1.0.0
servers:
  - url: http://localhost:4010
paths: {}
components:
  securitySchemes: {}
  schemas: {}
  responses: {}
```

Không dùng `openapi: 3.0.x`.

---

## 2. Path nên theo resource, không theo động từ

Đúng:

```text
GET /alerts/{alertId}
POST /events/sensor
POST /vision/detect
```

Không nên:

```text
GET /getAlertById
POST /createSensorEvent
POST /runDetection
```

---

## 3. Operation cần đủ thông tin

Mỗi operation cần có:

```yaml
operationId: createAlert
summary: Tạo cảnh báo mới
description: |
  Mô tả rõ service nào gọi, service nào nhận,
  dữ liệu đầu vào, dữ liệu đầu ra và tình huống lỗi.
tags: [alerts]
```

---

## 4. Không inline schema dài

Sai:

```yaml
schema:
  type: object
  properties:
    id:
      type: string
    message:
      type: string
```

Đúng:

```yaml
schema:
  $ref: '#/components/schemas/Alert'
```

---

## 5. Ràng buộc dữ liệu

Nên thêm constraint cho field:

| Loại | Constraint gợi ý |
|---|---|
| string | `minLength`, `maxLength`, `pattern`, `format` |
| number | `minimum`, `maximum`, `multipleOf` |
| array | `minItems`, `maxItems`, `uniqueItems` |
| object | `required`, `additionalProperties: false` |

---

## 6. Polymorphism

Lab 02 yêu cầu có ít nhất một phần dùng `oneOf` + `discriminator`.

Ví dụ:

```yaml
CampusEvent:
  oneOf:
    - $ref: '#/components/schemas/SensorEvent'
    - $ref: '#/components/schemas/AccessEvent'
  discriminator:
    propertyName: eventType
    mapping:
      SENSOR_READING: '#/components/schemas/SensorEvent'
      ACCESS_CHECK: '#/components/schemas/AccessEvent'
```

---

## 7. Union type với null

OpenAPI 3.1 không dùng `nullable: true`.

Sai:

```yaml
reason:
  type: string
  nullable: true
```

Đúng:

```yaml
reason:
  type: [string, "null"]
```

---

## 8. Error model chuẩn

Mọi lỗi 4xx/5xx nên dùng `application/problem+json` và schema `Problem`.

```yaml
responses:
  '400':
    $ref: '#/components/responses/BadRequest'
```

Trong `components/responses`:

```yaml
BadRequest:
  description: Dữ liệu không hợp lệ
  content:
    application/problem+json:
      schema:
        $ref: '#/components/schemas/Problem'
```

---

## 9. Lệnh kiểm tra

```bash
spectral lint openapi.yaml --ruleset campus-spectral.yaml
prism mock openapi.yaml --port 4010
```
