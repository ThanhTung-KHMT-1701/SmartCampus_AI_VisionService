# Git guide — one semester repository

## Create the portfolio first — once only

Before Lab 01:

1. On GitHub, select **New repository**.
2. Name it `FIT4110_<MãSinhViên>`, select **Public**, and select **Add a README file**.
3. Create the repository, copy its HTTPS URL, replace the example username/student ID below, and run:

```bash
git clone https://github.com/github-username/FIT4110_11223344.git
cd FIT4110_11223344
git status
git log --oneline -1
```

The README is the first commit, so Lab 01 can record your own Git history.

```text
FIT4110_<MãSinhViên>/
├── 01_Setup/
├── 02_OpenAPI/
├── 03_Postman/
├── 04_Docker/
├── 05_Compose/
└── 06_Plugathon/
```

The clone command sets `origin` automatically. Check it with `git remote -v`; do not change it for later labs.

## Move a completed lab into the portfolio

1. Clone the source starter separately and complete the lab there.
2. In Finder/File Explorer, create the matching folder inside `FIT4110_<MãSinhViên>` and copy the starter's **contents**, not the entire starter folder.
3. Do not copy the starter's hidden `.git` directory. **Never delete `FIT4110_<MãSinhViên>/.git`**; that is your portfolio history.
4. Do not rely on source GitHub Actions. Workflows under `02_OpenAPI/.github/workflows/` or another lab folder are not recognised by GitHub, and source workflows assume that their lab files are at the repository root.
5. Run the stated commands locally and keep reports/evidence in the lab folder.

> **Lab 01 exception:** copy `FIT4110_setup` contents into `01_Setup/` first, then run the evidence scripts from `01_Setup/`. Other labs may be completed in their separate starter folder before copying.

From the portfolio root:

```bash
git status
git add 03_Postman
git commit -m "lab03: add contract tests and evidence"
git push -u origin main
```

Use small, meaningful commits. Do not commit `.env`, tokens, private datasets, or generated dependency folders. After a lab deadline, preserve history and document any correction in a new commit.

---

## Bản tiếng Việt

# Git guide — một repository cho cả học kỳ

## Tạo portfolio trước — chỉ làm một lần

Trước Lab 01:

1. Trên GitHub, chọn **New repository**.
2. Đặt tên `FIT4110_<MãSinhViên>`, chọn **Public** và chọn **Add a README file**.
3. Tạo repository, sao chép HTTPS URL, thay username/MSSV trong ví dụ dưới đây rồi chạy:

```bash
git clone https://github.com/github-username/FIT4110_11223344.git
cd FIT4110_11223344
git status
git log --oneline -1
```

README là commit đầu tiên, vì vậy Lab 01 có thể ghi Git history của chính sinh viên.

```text
FIT4110_<MãSinhViên>/
├── 01_Setup/
├── 02_OpenAPI/
├── 03_Postman/
├── 04_Docker/
├── 05_Compose/
└── 06_Plugathon/
```

Lệnh clone tự đặt `origin`. Kiểm tra bằng `git remote -v`; không thay đổi `origin` ở các Lab sau.

## Đưa một Lab đã hoàn thành vào portfolio

1. Clone riêng starter nguồn và hoàn thành Lab tại đó.
2. Trong Finder/File Explorer, tạo thư mục tương ứng bên trong `FIT4110_<MãSinhViên>` rồi sao chép **nội dung** của starter, không sao chép nguyên cả thư mục starter.
3. Không sao chép thư mục `.git` ẩn của starter. **Tuyệt đối không xoá `FIT4110_<MãSinhViên>/.git`**; đây là lịch sử portfolio.
4. Không dựa vào GitHub Actions của starter. Workflow nằm dưới `02_OpenAPI/.github/workflows/` hoặc thư mục Lab khác sẽ không được GitHub nhận diện; workflow nguồn cũng giả định file của Lab nằm tại root repository.
5. Chạy các lệnh được yêu cầu tại local và lưu report/minh chứng trong thư mục Lab.

> **Ngoại lệ Lab 01:** sao chép nội dung `FIT4110_setup` vào `01_Setup/` trước, sau đó chạy evidence scripts từ `01_Setup/`. Các Lab khác có thể được hoàn thành trong thư mục starter riêng trước khi sao chép.

Từ root của portfolio:

```bash
git status
git add 03_Postman
git commit -m "lab03: add contract tests and evidence"
git push -u origin main
```

Dùng commit nhỏ, có ý nghĩa. Không commit `.env`, token, dữ liệu riêng tư hoặc thư mục dependency được sinh tự động. Sau mốc nộp Lab, giữ nguyên lịch sử và ghi lại mọi sửa đổi bằng commit mới.
