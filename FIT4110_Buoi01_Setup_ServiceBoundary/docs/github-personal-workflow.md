## Nộp bằng repository GitHub cá nhân

Sau khi giải nén và hoàn thành bài:

```bash
git init
git branch -M main
git add .
git commit -m "Complete FIT4110 lab"
git remote add origin https://github.com/<username>/FIT4110-<MSSV>.git
git push -u origin main
```

Repository nên để **Public** và đặt tên `FIT4110-<MSSV>` hoặc theo quy ước giảng viên.
Sinh viên mở link bằng cửa sổ ẩn danh để kiểm tra quyền truy cập, sau đó điền link vào Google Sheet.

Không commit `.env`, mật khẩu, token thật, `node_modules/`, `.venv/`, model hoặc dataset lớn.
