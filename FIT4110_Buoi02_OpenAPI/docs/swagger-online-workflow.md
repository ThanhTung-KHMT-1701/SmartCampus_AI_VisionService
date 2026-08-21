# Quy trình dùng Swagger Editor Online trong Lab 02

Lab 02 ưu tiên dùng Swagger Editor Online để sinh viên tập trung vào hợp đồng API thay vì cài thêm công cụ nặng.

Địa chỉ:

```text
https://editor.swagger.io
```

## 1. Khi nào dùng Swagger Editor Online?

Dùng trong các bước sau:

1. Soạn bản thảo `openapi.yaml` v0.9.
2. Xem preview API documentation ở bên phải.
3. Phát hiện lỗi YAML cơ bản.
4. Trao đổi với nhóm đối tác khi đàm phán field, schema, status code và example.
5. Xuất lại YAML để commit lên GitHub.

## 2. Cách làm

1. Mở `openapi.yaml` trong repo.
2. Copy toàn bộ nội dung file.
3. Mở `https://editor.swagger.io`.
4. Xóa nội dung mẫu bên trái.
5. Dán nội dung `openapi.yaml` của nhóm vào.
6. Chỉnh sửa contract theo user story và kết quả đàm phán.
7. Copy nội dung đã chỉnh về lại file `openapi.yaml` trong repo.
8. Chạy Spectral để kiểm tra rule của lớp.

## 3. Không dùng Swagger Editor thay cho Spectral

Swagger Editor Online giúp kiểm tra cú pháp và preview tài liệu, nhưng không thay thế được ruleset của lớp.

Sau khi sửa xong, vẫn phải chạy:

```bash
spectral lint openapi.yaml --ruleset campus-spectral.yaml
```

Xuất report nộp bài:

```bash
spectral lint openapi.yaml --ruleset campus-spectral.yaml --format text > evidence/buoi-02/spectral-report.txt
```

## 4. Không dùng Postman trong Lab 02

Lab 02 chưa yêu cầu Postman.

Phần kiểm thử mock server dùng:

- Prism để dựng mock server từ `openapi.yaml`;
- `curl` để gửi 5 request mẫu;
- ảnh chụp Terminal/PowerShell làm minh chứng.

Quy trình:

```bash
prism mock openapi.yaml --port 4010
```

Mở terminal thứ hai và gọi thử:

```bash
curl -i http://localhost:4010/health
curl -i http://localhost:4010/alerts/recent -H "Authorization: Bearer test-token"
```

Hoặc chạy script mẫu:

```bash
./scripts/test_mock_with_curl.sh
```

Windows:

```powershell
.\scripts\test_mock_with_curl.ps1
```

## 5. Lưu ý khi muốn dùng nút Try it out trên Swagger Online

Không khuyến khích dùng `Try it out` làm minh chứng chính trong Lab 02, vì trình duyệt có thể bị chặn bởi CORS hoặc khác biệt giữa môi trường online và mock server cục bộ.

Minh chứng chính nên là:

```text
Swagger Editor Online: ảnh preview hoặc ảnh lỗi YAML nếu cần
Spectral: evidence/buoi-02/spectral-report.txt
Prism + curl: 5 ảnh chụp request/response
```
