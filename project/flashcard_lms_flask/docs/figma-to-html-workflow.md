# Quy trình chuyển thiết kế Figma thành HTML/CSS cho Flashcard LMS

## Nguyên tắc

Không nên coi thao tác Export trong Figma là xuất toàn bộ website Flask hoàn chỉnh.
Figma hỗ trợ kiểm tra thông số thiết kế, sao chép một số đoạn code gợi ý và xuất tài nguyên.
HTML template, CSS responsive, hành vi JavaScript, xác thực và kết nối MySQL vẫn cần được triển khai trong project.

## 1. Chuẩn bị frame trong Figma

Đặt tên frame rõ ràng theo trang:
- `Lecturer / Dashboard`
- `Lecturer / Courses`
- `Lecturer / Course Form`
- `Lecturer / Lessons`
- `Lecturer / Enrollment Requests`
- `Lecturer / Students`

Mỗi trang nên có frame desktop. Nếu đã thiết kế mobile, đặt tên rõ:
- `Lecturer / Dashboard / Desktop`
- `Lecturer / Dashboard / Mobile`

## 2. Dùng Dev Mode để lấy thông số

1. Mở file Figma.
2. Chọn frame cần code.
3. Nhấn `Shift + D` để vào Dev Mode.
4. Chọn từng component/layer và ghi lại:
   - Width / height
   - Padding / gap / alignment
   - Font family / size / weight / line height
   - Text color / background / border
   - Border radius / shadow
   - Responsive behavior nếu có

Không nên copy một đoạn CSS của cả frame rồi xem đó là code hoàn chỉnh. Hãy dùng thông số để triển khai lại bằng layout HTML/CSS có cấu trúc.

## 3. Export tài nguyên

Chọn icon, logo, hình minh họa hoặc avatar:
1. Chọn layer.
2. Trong phần Export, nhấn `+`.
3. Chọn SVG cho icon/vector; PNG hoặc JPG cho ảnh raster.
4. Export và lưu vào `app/static/images/`.

Đặt tên dễ hiểu, ví dụ:
- `logo-flashcard.svg`
- `icon-course.svg`
- `illustration-empty-course.png`

Không export text thành hình ảnh nếu text đó cần tìm kiếm, truy cập hoặc thay đổi bằng code.

## 4. Ánh xạ Figma sang project Flask

| Thiết kế Figma | Vị trí trong project |
|---|---|
| Sidebar dùng chung | `app/templates/base.html` |
| Header dùng chung | `app/templates/base.html` |
| Lecturer Dashboard | `app/templates/lecturer/dashboard.html` |
| Danh sách khóa học | `app/templates/lecturer/courses.html` |
| Form khóa học | `app/templates/lecturer/course_form.html` |
| Danh sách/builder bài học | `app/templates/lecturer/lessons.html` |
| CSS dùng chung | `app/static/css/app.css` |
| JavaScript dùng chung | `app/static/js/app.js` |
| Hình/icon export từ Figma | `app/static/images/` |

## 5. Cách code để khớp thiết kế

- Dùng CSS variables cho màu, font, radius và spacing.
- Dùng Flexbox/Grid cho bố cục; hạn chế đặt `position:absolute` cho toàn trang.
- Dùng Jinja2 `extends` và `include` để tái sử dụng Sidebar/Header.
- Dùng HTML semantic: `nav`, `main`, `section`, `form`, `table`, `button`.
- Kiểm tra desktop và mobile ở đúng kích thước frame trong Figma.
- Đối chiếu bằng screenshot: Figma ở một bên, trình duyệt ở bên còn lại.
- Sửa theo thứ tự: bố cục tổng thể → khoảng cách → typography → màu/viền → icon/ảnh → responsive.

## 6. Dùng plugin tạo code tự động (không bắt buộc)

Các plugin như Anima có thể tạo HTML/CSS ban đầu từ Figma. Hãy xem đó là scaffold để tham khảo, không phải sản phẩm Flask hoàn chỉnh:
- Kiểm tra và bỏ markup dư thừa.
- Chuyển các phần lặp lại thành Jinja components.
- Thay dữ liệu tĩnh bằng dữ liệu từ Flask.
- Thay các button/link giả bằng route hoặc form thực.
- Kiểm tra accessibility, responsive và bảo mật.

## 7. Lưu bằng Git để giảng viên so sánh

- Giữ ảnh export thiết kế trong `docs/design/` (chỉ ảnh thiết kế, không chứa dữ liệu cá nhân).
- Ghi link Figma trong `docs/design/README.md` nếu file được phép chia sẻ.
- Mỗi tính năng nên có commit riêng.
- Không đưa `.env`, mật khẩu MySQL, API key, dữ liệu người dùng hoặc SQL dump có dữ liệu nhạy cảm lên repository.
