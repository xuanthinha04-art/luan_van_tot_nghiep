<!-- Lưu ý: Khi bạn dùng lệnh python -m flask --app run.py run --debug, Flask import file này và sử dụng biến app. Nó không chạy phần if __name__ == "__main__" như khi bạn chạy trực tiếp python run.py. -->
# Flashcard LMS – Flask Lecturer MVP

Starter project cho giai đoạn triển khai giao diện và Backend Lecturer. Ứng dụng dùng trực tiếp Database MySQL `flashcard_lms` đã tạo; **không tự tạo, xóa hoặc migrate lại 36 bảng**.

## Chức năng đã có trong bản đầu

- Đăng nhập bằng bảng `users` và `roles`; chỉ tài khoản `LECTURER` được vào khu vực Lecturer.
- Dashboard lấy số liệu trực tiếp từ MySQL.
- Danh sách, tìm kiếm và lọc khóa học.
- Tạo và chỉnh sửa khóa học.
- Kiểm tra ngôn ngữ/chủ đề nhất quán khi lưu khóa học.
- Quản lý bài học: tạo bài học, nhập nội dung lý thuyết.
- Gắn bộ Flashcard có cùng ngôn ngữ vào bài học.
- Xuất bản khóa học khi có ít nhất một bài học hợp lệ.
- Xem yêu cầu tham gia; duyệt hoặc từ chối.
- Xem danh sách học viên đã được duyệt.

## 1. Yêu cầu

- Windows 10/11
- Python 3.11 trở lên
- MySQL đang chạy
- Database `flashcard_lms` đã được tạo và có các bảng theo file SQL của dự án


## 2. Mở project trong VS Code

Giải nén ZIP, mở thư mục `flashcard_lms_flask` bằng VS Code.

Mở Terminal tại thư mục project và chạy:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn kích hoạt môi trường:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## 3. Cấu hình kết nối MySQL

Tạo file `.env` bằng cách sao chép `.env.example`:

```powershell
Copy-Item .env.example .env
```

Mở `.env`, điền đúng tài khoản MySQL trên máy bạn:

```env
SECRET_KEY=replace-with-a-long-random-secret
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=flashcard_lms
DB_USER=root
DB_PASSWORD=mat_khau_mysql_cua_ban
```

Nếu MySQL không có mật khẩu root, để `DB_PASSWORD=`.

**Không commit file `.env` lên GitHub.** File này đã được thêm vào `.gitignore`.

## 4. Tạo tài khoản Lecturer thử nghiệm

Lệnh này tạo một tài khoản trực tiếp trong bảng `users`, dùng password hash của Werkzeug và role đã có trong bảng `roles`. Nó không tạo tài khoản qua một URL công khai.

```powershell
flask --app run.py create-lecturer
```

Nhập họ tên, email và mật khẩu khi được hỏi.

Nếu bạn đã có tài khoản Lecturer với mật khẩu được hash tương thích, có thể dùng tài khoản đó và bỏ qua bước này.

## 5. Chạy ứng dụng

```powershell
flask --app run.py run --debug
```

Mở trình duyệt tại:

```text
http://127.0.0.1:5000
```

Kiểm tra kết nối Database:

```text
http://127.0.0.1:5000/health/db
```

Nếu kết nối thành công, endpoint trả về `ok: true`, tên Database và phiên bản MySQL.

## 6. Cấu trúc thư mục

```text
flashcard_lms_flask/
├── app/
│   ├── auth/
│   ├── lecturer/
│   ├── templates/
│   └── static/
├── config.py
├── run.py
├── requirements.txt
├── .env.example
└── README.md
```

## 7. Đẩy source lên GitHub

Tạo một repository mới, ví dụ `flashcard-lms`.

Trong Terminal tại thư mục project:

```powershell
git init
git add .
git commit -m "Initial Flask Lecturer MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/flashcard-lms.git
git push -u origin main
```

Thay `YOUR_USERNAME` bằng username GitHub của bạn. Nếu đã có remote `origin`, không chạy lại lệnh `git remote add`.

Sau mỗi phần code hoàn thành:

```powershell
git add .
git commit -m "Build lecturer course management"
git push
```

Giảng viên có thể xem source HTML trong `app/templates/`, CSS trong `app/static/css/`, JavaScript trong `app/static/js/` và lịch sử commit.

## 8. Quy ước làm việc

- Không đưa mật khẩu DB, `.env`, dữ liệu người dùng thật hoặc bản dump có thông tin nhạy cảm lên repository công khai.
- Không import lại `flashcard_lms.sql` vào Database đang chạy vì bản dump có `DROP TABLE IF EXISTS`.
- Không dùng `db.create_all()`; project này kết nối schema có sẵn.
- Dùng parameterized SQL qua SQLAlchemy `text()`; không nối chuỗi trực tiếp từ dữ liệu người dùng.
- Các route Lecturer đều kiểm tra đăng nhập và role; các thao tác cập nhật khóa học kiểm tra quyền owner/assigned lecturer.
- Đây là MVP đang phát triển, cần tiếp tục kiểm thử trên Database máy bạn và đối chiếu từng frame Figma trước khi coi là bản hoàn chỉnh.

## 9. Chuyển thiết kế Figma thành HTML/CSS

Xem hướng dẫn chi tiết tại `docs/figma-to-html-workflow.md`.
Đặt ảnh export thiết kế trong `docs/design/` để giảng viên tiện đối chiếu với giao diện đã code.

## 10. Bảo vệ Database trước khi push

Không commit file dump SQL chứa lệnh `DROP TABLE`, dữ liệu tài khoản hoặc dữ liệu thật. `.gitignore` đã loại các file `*.sql` theo mặc định. Nếu cần nộp cấu trúc Database cho giảng viên, dùng ERD `.drawio`/ảnh ERD hoặc tạo một bản schema đã làm sạch riêng.
