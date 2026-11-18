# Từ điển Database Flashcard LMS (Tiếng Việt)

> Tài liệu này giải thích tên bảng và cột bằng tiếng Việt. Tên bảng/cột trong MySQL vẫn giữ nguyên tiếng Anh để nhất quán với source code. Nội dung được đối chiếu từ file cấu trúc `flashcard_lms.sql` mà bạn đã cung cấp.

## Quy ước
- `PK`: Khóa chính (Primary Key).
- `FK`: Khóa ngoại (Foreign Key).
- `UNIQUE`: Giá trị hoặc tổ hợp giá trị không được trùng.
- `NULL`: Có thể không có giá trị.
- Các trường `*_id` thường là mã định danh/liên kết; cần đọc cùng phần mô tả quan hệ.

## Nhóm 1 – Tài khoản và vai trò

### `roles` — Vai trò
Danh mục vai trò tài khoản trong hệ thống: ADMIN, LECTURER, LEARNER.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `role_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã vai trò của tài khoản. |
| `role_name` | `VARCHAR(50)` | NOT NULL | Tên vai trò, ví dụ ADMIN, LECTURER hoặc LEARNER. |
| `description` | `VARCHAR(255)` | NULL, DEFAULT NULL | Mô tả nội dung hoặc mục đích. |

**Ràng buộc UNIQUE:** (`role_name`).

### `users` — Người dùng
Lưu tài khoản, thông tin hồ sơ, mật khẩu đã băm, vai trò và trạng thái tài khoản.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `user_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã tài khoản người dùng. |
| `full_name` | `VARCHAR(100)` | NOT NULL | Họ và tên người dùng. |
| `email` | `VARCHAR(255)` | NOT NULL | Địa chỉ email đăng nhập; phải duy nhất. |
| `password_hash` | `VARCHAR(255)` | NOT NULL | Mật khẩu đã được băm, không lưu mật khẩu gốc. |
| `avatar_url` | `VARCHAR(500)` | NULL, DEFAULT NULL | Đường dẫn ảnh đại diện. |
| `role_id` | `INT UNSIGNED` | FK → `roles.role_id`, NOT NULL | Mã vai trò của tài khoản. |
| `account_status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'ACTIVE' | Trạng thái tài khoản, ví dụ ACTIVE, LOCKED, DEACTIVATED. |
| `registered_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm đăng ký tài khoản. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`email`).

### `lecturer_requests` — Yêu cầu trở thành giảng viên
Lưu hồ sơ người dùng đề nghị nâng cấp vai trò Lecturer và kết quả xét duyệt của Admin.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `request_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã yêu cầu trở thành giảng viên. |
| `user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `specialization` | `VARCHAR(150)` | NOT NULL | Chuyên môn của người xin trở thành giảng viên. |
| `experience_years` | `INT UNSIGNED` | NULL, DEFAULT NULL | Số năm kinh nghiệm. |
| `professional_info` | `TEXT` | NULL | Thông tin nghề nghiệp/chứng chỉ liên quan. |
| `introduction` | `TEXT` | NULL | Phần giới thiệu của người đăng ký. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'PENDING' | Trạng thái yêu cầu giảng viên, dùng để theo dõi chờ duyệt/đã duyệt/từ chối. |
| `reviewed_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người xét duyệt/xử lý. |
| `reviewed_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm thực hiện lần ôn. |
| `review_note` | `TEXT` | NULL | Ghi chú của Admin khi xét duyệt. |
| `submitted_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm gửi hồ sơ. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

### `lecturer_request_documents` — Tài liệu minh chứng giảng viên
Lưu các tài liệu người dùng đính kèm cho một yêu cầu trở thành giảng viên.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `document_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã tài liệu minh chứng. |
| `request_id` | `INT UNSIGNED` | FK → `lecturer_requests.request_id`, NOT NULL | Mã yêu cầu trở thành giảng viên. |
| `file_name` | `VARCHAR(255)` | NOT NULL | Tên tệp minh chứng. |
| `file_url` | `VARCHAR(500)` | NOT NULL | Đường dẫn lưu tệp. |
| `file_type` | `VARCHAR(100)` | NULL, DEFAULT NULL | Loại/định dạng tệp. |
| `uploaded_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tải tệp lên. |

## Nhóm 2 – Ngôn ngữ, chủ đề và từ vựng

### `languages` — Ngôn ngữ
Danh mục ngôn ngữ hệ thống hỗ trợ học, ví dụ English, Chinese, Japanese.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `language_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã ngôn ngữ. |
| `language_name` | `VARCHAR(100)` | NOT NULL | Tên ngôn ngữ. |
| `language_code` | `VARCHAR(10)` | NOT NULL | Mã ngôn ngữ, ví dụ en, zh, ja. |
| `description` | `TEXT` | NULL | Mô tả nội dung hoặc mục đích. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'ACTIVE' | Trạng thái ngôn ngữ ACTIVE/INACTIVE. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`language_code`).

### `topics` — Chủ đề
Danh mục chủ đề thuộc một ngôn ngữ, có thể có cấp độ và người tạo.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `topic_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã chủ đề của khóa học hoặc nội dung. |
| `topic_name` | `VARCHAR(150)` | NOT NULL | Tên chủ đề. |
| `description` | `TEXT` | NULL | Mô tả nội dung hoặc mục đích. |
| `language_id` | `INT UNSIGNED` | FK → `languages.language_id`, NOT NULL | Mã ngôn ngữ. |
| `level` | `VARCHAR(30)` | NULL, DEFAULT NULL | Cấp độ của chủ đề. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'ACTIVE' | Trạng thái chủ đề ACTIVE/INACTIVE. |
| `created_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người dùng tạo bản ghi. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`language_id`, `topic_name`); (`language_id`, `topic_id`).

### `user_learning_languages` — Ngôn ngữ người dùng đang học
Bảng liên kết người dùng với các ngôn ngữ đăng ký học và chủ đề hiện chọn cho từng ngôn ngữ.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `user_id` | `INT UNSIGNED` | PK, FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `language_id` | `INT UNSIGNED` | PK, FK → `topics.language_id`, NOT NULL | Mã ngôn ngữ. |
| `selected_topic_id` | `INT UNSIGNED` | FK → `topics.topic_id`, NULL, DEFAULT NULL | Mã chủ đề người dùng đang chọn trong ngôn ngữ này. |
| `is_current` | `TINYINT(1)` | NOT NULL, DEFAULT '0' | Đánh dấu đây có phải ngôn ngữ hiện tại người dùng đang học hay không. |
| `started_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm người dùng bắt đầu học ngôn ngữ. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

### `vocabulary_sets` — Bộ từ vựng
Lưu bộ từ vựng cá nhân, bộ chung hoặc bộ do giảng viên tạo, kèm ngôn ngữ/chủ đề và chủ sở hữu.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `set_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã bộ từ vựng/Flashcard. |
| `set_name` | `VARCHAR(200)` | NOT NULL | Tên bộ từ vựng. |
| `description` | `TEXT` | NULL | Mô tả nội dung hoặc mục đích. |
| `set_type` | `VARCHAR(30)` | NOT NULL | Loại bộ: cá nhân, chung hoặc do giảng viên tạo. |
| `language_id` | `INT UNSIGNED` | FK → `topics.language_id`, NOT NULL | Mã ngôn ngữ. |
| `topic_id` | `INT UNSIGNED` | FK → `topics.topic_id`, NULL, DEFAULT NULL | Mã chủ đề của khóa học hoặc nội dung. |
| `owner_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người sở hữu bộ từ vựng. |
| `created_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người dùng tạo bản ghi. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'ACTIVE' | Trạng thái bộ từ vựng, ví dụ ACTIVE/INACTIVE. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

### `vocabulary_items` — Từ vựng / Flashcard
Lưu một từ hoặc cụm từ, nghĩa, ví dụ, ảnh minh họa và thứ tự trong bộ từ vựng.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `item_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã từ vựng/Flashcard. |
| `set_id` | `INT UNSIGNED` | FK → `vocabulary_sets.set_id`, NOT NULL | Mã bộ từ vựng/Flashcard. |
| `term` | `VARCHAR(255)` | NOT NULL | Từ hoặc cụm từ cần học. |
| `meaning` | `TEXT` | NOT NULL | Nghĩa/định nghĩa của từ. |
| `example` | `TEXT` | NULL | Câu ví dụ sử dụng từ. |
| `image_url` | `VARCHAR(500)` | NULL, DEFAULT NULL | Đường dẫn ảnh minh họa từ vựng. |
| `display_order` | `INT UNSIGNED` | NOT NULL, DEFAULT '1' | Thứ tự hiển thị. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'ACTIVE' | Trạng thái từ vựng, ví dụ ACTIVE/INACTIVE. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`set_id`, `display_order`).

### `vocabulary_reports` — Báo lỗi từ vựng
Lưu báo cáo của người dùng về từ vựng sai hoặc cần chỉnh sửa và quá trình xử lý.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `report_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã báo cáo từ vựng. |
| `item_id` | `INT UNSIGNED` | FK → `vocabulary_items.item_id`, NOT NULL | Mã từ vựng/Flashcard. |
| `reported_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã người gửi báo lỗi. |
| `report_content` | `TEXT` | NOT NULL | Nội dung mô tả lỗi từ vựng. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'PENDING' | Trạng thái xử lý báo lỗi từ vựng. |
| `reviewed_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người xét duyệt/xử lý. |
| `reviewed_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm thực hiện lần ôn. |
| `admin_note` | `TEXT` | NULL | Ghi chú xử lý của Admin. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

## Nhóm 3 – Khóa học và bài học

### `courses` — Khóa học
Lưu thông tin khóa học do giảng viên tạo, ngôn ngữ, chủ đề, người tạo và trạng thái xuất bản.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `course_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã khóa học. |
| `course_name` | `VARCHAR(200)` | NOT NULL | Tên khóa học. |
| `description` | `TEXT` | NULL | Mô tả nội dung hoặc mục đích. |
| `language_id` | `INT UNSIGNED` | FK → `topics.language_id`, NOT NULL | Mã ngôn ngữ. |
| `topic_id` | `INT UNSIGNED` | FK → `topics.topic_id`, NULL, DEFAULT NULL | Mã chủ đề của khóa học hoặc nội dung. |
| `created_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã người dùng tạo bản ghi. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'DRAFT' | Trạng thái khóa học: DRAFT, PUBLISHED hoặc UNPUBLISHED. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

### `course_lecturers` — Giảng viên được phân công
Bảng trung gian ghi nhận giảng viên được phân công vào khóa học và quyền VIEW/EDIT.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `course_lecturer_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Trường lưu thông tin nghiệp vụ liên quan; cần kiểm tra cùng chức năng của bảng. |
| `course_id` | `INT UNSIGNED` | FK → `courses.course_id`, NOT NULL | Mã khóa học. |
| `lecturer_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản giảng viên được phân công. |
| `assigned_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người thực hiện phân công. |
| `permission` | `VARCHAR(30)` | NOT NULL, DEFAULT 'EDIT' | Quyền của giảng viên được phân công, ví dụ VIEW hoặc EDIT. |
| `assigned_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm phân công giảng viên. |

**Ràng buộc UNIQUE:** (`course_id`, `lecturer_user_id`).

### `enrollments` — Đăng ký khóa học
Lưu từng yêu cầu học viên xin tham gia khóa học, trạng thái duyệt, người duyệt và lý do từ chối.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `enrollment_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Trường lưu thông tin nghiệp vụ liên quan; cần kiểm tra cùng chức năng của bảng. |
| `course_id` | `INT UNSIGNED` | FK → `courses.course_id`, NOT NULL | Mã khóa học. |
| `learner_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản học viên gửi yêu cầu tham gia. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'PENDING' | Trạng thái yêu cầu: PENDING, APPROVED, REJECTED hoặc CANCELLED. |
| `requested_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm gửi yêu cầu đăng ký. |
| `reviewed_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người xét duyệt/xử lý. |
| `reviewed_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm thực hiện lần ôn. |
| `rejection_reason` | `TEXT` | NULL | Lý do từ chối yêu cầu tham gia. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

### `lessons` — Bài học
Lưu bài học thuộc một khóa học, nội dung lý thuyết, thứ tự và trạng thái.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `lesson_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã bài học. |
| `course_id` | `INT UNSIGNED` | FK → `courses.course_id`, NOT NULL | Mã khóa học. |
| `lesson_name` | `VARCHAR(200)` | NOT NULL | Tên bài học. |
| `description` | `TEXT` | NULL | Mô tả nội dung hoặc mục đích. |
| `theory_content` | `LONGTEXT` | NULL | Nội dung lý thuyết của bài học. |
| `lesson_order` | `INT UNSIGNED` | NOT NULL, DEFAULT '1' | Thứ tự bài học trong khóa học. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'DRAFT' | Trạng thái bài học: DRAFT, PUBLISHED hoặc HIDDEN. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`course_id`, `lesson_order`).

### `lesson_vocabulary_sets` — Bộ Flashcard trong bài học
Bảng trung gian liên kết bài học với các bộ Flashcard; cho phép một bài học có nhiều bộ và một bộ dùng lại ở nhiều bài.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `lesson_vocabulary_set_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã liên kết giữa bài học và bộ Flashcard. |
| `lesson_id` | `INT UNSIGNED` | FK → `lessons.lesson_id`, NOT NULL | Mã bài học. |
| `set_id` | `INT UNSIGNED` | FK → `vocabulary_sets.set_id`, NOT NULL | Mã bộ từ vựng/Flashcard. |
| `display_order` | `INT UNSIGNED` | NOT NULL, DEFAULT '1' | Thứ tự hiển thị. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |

**Ràng buộc UNIQUE:** (`lesson_id`, `set_id`); (`lesson_id`, `display_order`).

## Nhóm 4 – Tiến độ và ôn tập

### `learning_progress` — Tiến độ ghi nhớ từ vựng
Lưu trạng thái ghi nhớ hiện tại của từng từ đối với từng người học.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `progress_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã bản ghi tiến độ học từ. |
| `user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `item_id` | `INT UNSIGNED` | FK → `vocabulary_items.item_id`, NOT NULL | Mã từ vựng/Flashcard. |
| `memory_status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'NEW' | Trạng thái ghi nhớ hiện tại: NEW, NOT_REMEMBERED, LEARNING, REMEMBERED. |
| `last_reviewed_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm ôn từ gần nhất. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`user_id`, `item_id`).

### `review_schedules` — Lịch ôn hiện tại
Lưu thời điểm cần ôn tiếp theo và trạng thái lịch của một bản ghi tiến độ.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `schedule_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã lịch ôn tập. |
| `progress_id` | `INT UNSIGNED` | FK → `learning_progress.progress_id`, NOT NULL | Mã bản ghi tiến độ học từ. |
| `next_review_at` | `DATETIME` | NOT NULL | Thời điểm cần ôn tiếp theo. |
| `schedule_status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'ACTIVE' | Trạng thái lịch: ACTIVE, PAUSED hoặc COMPLETED. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`progress_id`).

### `review_sessions` — Lịch sử ôn tập
Lưu từng lần người học ôn một từ, trạng thái trước/sau và thời lượng ôn.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `session_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã lần ôn tập. |
| `progress_id` | `INT UNSIGNED` | FK → `learning_progress.progress_id`, NOT NULL | Mã bản ghi tiến độ học từ. |
| `previous_status` | `VARCHAR(30)` | NOT NULL | Trạng thái ghi nhớ trước lần ôn. |
| `new_status` | `VARCHAR(30)` | NOT NULL | Trạng thái ghi nhớ sau lần ôn. |
| `reviewed_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm thực hiện lần ôn. |
| `duration_seconds` | `INT UNSIGNED` | NULL, DEFAULT NULL | Thời lượng thực hiện, tính bằng giây. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |

### `study_reminder_settings` — Cài đặt nhắc nhở học tập
Lưu trạng thái bật/tắt, giờ nhắc và múi giờ của từng người dùng.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `setting_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã cấu hình nhắc nhở. |
| `user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `reminder_enabled` | `TINYINT(1)` | NOT NULL, DEFAULT '1' | Cho biết người dùng có bật nhắc nhở hay không. |
| `reminder_time` | `TIME` | NOT NULL, DEFAULT '20:00:00' | Giờ gửi nhắc nhở trong ngày. |
| `timezone` | `VARCHAR(64)` | NOT NULL, DEFAULT 'Asia/Ho_Chi_Minh' | Múi giờ áp dụng cho giờ nhắc. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`user_id`).

### `study_reminder_days` — Ngày nhận nhắc nhở học tập
Lưu các thứ trong tuần mà người dùng chọn để nhận email nhắc học.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `reminder_day_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã ngày nhắc nhở. |
| `setting_id` | `INT UNSIGNED` | FK → `study_reminder_settings.setting_id`, NOT NULL | Mã cấu hình nhắc nhở. |
| `weekday` | `TINYINT UNSIGNED` | NOT NULL | Ngày trong tuần được chọn. Theo quy ước dự án: 1=Thứ Hai đến 7=Chủ Nhật. |

**Ràng buộc UNIQUE:** (`setting_id`, `weekday`).

## Nhóm 5 – Bài kiểm tra và kết quả

### `assessments` — Bài kiểm tra
Lưu thông tin bài kiểm tra, loại bài, loại câu hỏi, khóa học/chủ đề liên quan và người tạo.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `assessment_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã bài kiểm tra. |
| `assessment_name` | `VARCHAR(200)` | NOT NULL | Tên bài kiểm tra. |
| `description` | `TEXT` | NULL | Mô tả nội dung hoặc mục đích. |
| `assessment_type` | `VARCHAR(30)` | NOT NULL | Loại bài: COURSE, PLACEMENT hoặc PRACTICE. |
| `question_type` | `VARCHAR(30)` | NOT NULL | Loại câu hỏi sử dụng trong bài kiểm tra. |
| `course_id` | `INT UNSIGNED` | FK → `courses.course_id`, NULL, DEFAULT NULL | Mã khóa học. |
| `topic_id` | `INT UNSIGNED` | FK → `topics.topic_id`, NULL, DEFAULT NULL | Mã chủ đề của khóa học hoặc nội dung. |
| `created_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã người dùng tạo bản ghi. |
| `duration_minutes` | `INT UNSIGNED` | NULL, DEFAULT NULL | Thời gian làm bài tối đa, tính bằng phút. |
| `total_points` | `DECIMAL(8,2)` | NOT NULL, DEFAULT '0.00' | Tổng điểm tối đa. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'DRAFT' | Trạng thái bài kiểm tra: DRAFT, PUBLISHED hoặc ARCHIVED. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

### `questions` — Câu hỏi
Lưu nội dung từng câu hỏi thuộc một bài kiểm tra, giải thích, điểm và thứ tự hiển thị.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `question_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã câu hỏi. |
| `assessment_id` | `INT UNSIGNED` | FK → `assessments.assessment_id`, NOT NULL | Mã bài kiểm tra. |
| `question_content` | `LONGTEXT` | NOT NULL | Nội dung câu hỏi. |
| `explanation` | `TEXT` | NULL | Giải thích đáp án/câu hỏi. |
| `points` | `DECIMAL(8,2)` | NOT NULL, DEFAULT '1.00' | Điểm tối đa của câu hỏi. |
| `display_order` | `INT UNSIGNED` | NOT NULL, DEFAULT '1' | Thứ tự hiển thị. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`assessment_id`, `display_order`).

### `question_options` — Lựa chọn trắc nghiệm
Lưu các phương án trả lời của câu hỏi trắc nghiệm và đánh dấu phương án đúng.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `option_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã lựa chọn trắc nghiệm. |
| `question_id` | `INT UNSIGNED` | FK → `questions.question_id`, NOT NULL | Mã câu hỏi. |
| `option_content` | `TEXT` | NOT NULL | Nội dung phương án trả lời. |
| `is_correct` | `TINYINT(1)` | NOT NULL, DEFAULT '0' | Đánh dấu đáp án đúng hoặc câu trả lời đúng. |
| `display_order` | `INT UNSIGNED` | NOT NULL, DEFAULT '1' | Thứ tự hiển thị. |

**Ràng buộc UNIQUE:** (`question_id`, `display_order`).

### `question_expected_answers` — Đáp án chấp nhận cho câu điền từ
Lưu đáp án chuẩn và các biến thể đáp án được chấp nhận cho câu hỏi điền từ.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `expected_answer_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã đáp án được chấp nhận. |
| `question_id` | `INT UNSIGNED` | FK → `questions.question_id`, NOT NULL | Mã câu hỏi. |
| `answer_content` | `VARCHAR(1000)` | NOT NULL | Nội dung đáp án hoặc câu trả lời dạng văn bản. |
| `is_primary` | `TINYINT(1)` | NOT NULL, DEFAULT '0' | Đánh dấu đây là đáp án chính. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |

### `question_matching_pairs` — Các cặp nối
Lưu hai vế nội dung tương ứng của từng câu hỏi dạng nối cặp.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `pair_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã cặp nội dung dùng trong câu MATCHING. |
| `question_id` | `INT UNSIGNED` | FK → `questions.question_id`, NOT NULL | Mã câu hỏi. |
| `left_content` | `TEXT` | NOT NULL | Nội dung vế trái của cặp nối. |
| `right_content` | `TEXT` | NOT NULL | Nội dung vế phải tương ứng. |
| `display_order` | `INT UNSIGNED` | NOT NULL, DEFAULT '1' | Thứ tự hiển thị. |

**Ràng buộc UNIQUE:** (`question_id`, `display_order`).

### `assessment_attempts` — Lượt làm bài
Mỗi lần một học viên thực hiện bài kiểm tra được lưu thành một lượt riêng, kèm số lần làm, trạng thái và điểm.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `attempt_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã lượt làm bài. |
| `assessment_id` | `INT UNSIGNED` | FK → `assessments.assessment_id`, NOT NULL | Mã bài kiểm tra. |
| `user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `attempt_number` | `INT UNSIGNED` | NOT NULL | Số thứ tự lượt làm bài của người dùng. |
| `started_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm người dùng bắt đầu học ngôn ngữ. |
| `submitted_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm gửi hồ sơ. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'IN_PROGRESS' | Trạng thái lượt làm: IN_PROGRESS, SUBMITTED, WAITING_GRADING, GRADED hoặc CANCELLED. |
| `total_questions` | `INT UNSIGNED` | NOT NULL, DEFAULT '0' | Tổng số câu hỏi trong lượt làm. |
| `correct_answers` | `INT UNSIGNED` | NOT NULL, DEFAULT '0' | Số câu được chấm đúng. |
| `score` | `DECIMAL(8,2)` | NULL, DEFAULT NULL | Điểm đạt được. |
| `total_points` | `DECIMAL(8,2)` | NOT NULL, DEFAULT '0.00' | Tổng điểm tối đa. |
| `duration_seconds` | `INT UNSIGNED` | NULL, DEFAULT NULL | Thời lượng thực hiện, tính bằng giây. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |

**Ràng buộc UNIQUE:** (`assessment_id`, `user_id`, `attempt_number`).

### `student_answers` — Câu trả lời của học viên
Lưu câu trả lời cho từng câu hỏi trong một lượt làm bài, kết quả và thông tin chấm điểm.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `student_answer_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã câu trả lời của học viên. |
| `attempt_id` | `INT UNSIGNED` | FK → `assessment_attempts.attempt_id`, NOT NULL | Mã lượt làm bài. |
| `question_id` | `INT UNSIGNED` | FK → `questions.question_id`, NOT NULL | Mã câu hỏi. |
| `selected_option_id` | `INT UNSIGNED` | FK → `question_options.option_id`, NULL, DEFAULT NULL | Mã phương án trắc nghiệm mà học viên chọn. |
| `answer_content` | `LONGTEXT` | NULL | Nội dung đáp án hoặc câu trả lời dạng văn bản. |
| `is_correct` | `TINYINT(1)` | NULL, DEFAULT NULL | Đánh dấu đáp án đúng hoặc câu trả lời đúng. |
| `score` | `DECIMAL(8,2)` | NULL, DEFAULT NULL | Điểm đạt được. |
| `grading_status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'PENDING' | Trạng thái chấm: PENDING, AUTO_GRADED, AI_GRADED, MANUALLY_GRADED hoặc NOT_GRADED. |
| `lecturer_feedback` | `TEXT` | NULL | Nhận xét của giảng viên về câu trả lời. |
| `answered_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm học viên trả lời câu hỏi. |
| `graded_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm câu trả lời được chấm. |

**Ràng buộc UNIQUE:** (`attempt_id`, `question_id`).

### `student_matching_answers` — Lựa chọn nối cặp của học viên
Lưu mỗi cặp ghép mà học viên chọn cho một câu trả lời dạng MATCHING.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `matching_answer_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã bản ghi lựa chọn nối cặp của học viên. |
| `student_answer_id` | `INT UNSIGNED` | FK → `student_answers.student_answer_id`, NOT NULL | Mã câu trả lời của học viên. |
| `left_pair_id` | `INT UNSIGNED` | FK → `question_matching_pairs.pair_id`, NOT NULL | Mã cặp được chọn ở vế trái. |
| `selected_right_pair_id` | `INT UNSIGNED` | FK → `question_matching_pairs.pair_id`, NOT NULL | Mã cặp được chọn ở vế phải. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |

**Ràng buộc UNIQUE:** (`student_answer_id`, `left_pair_id`); (`student_answer_id`, `selected_right_pair_id`).

## Nhóm 6 – AI và thanh toán

### `ai_packages` — Gói AI
Danh mục các gói AI mà người dùng có thể đăng ký, gồm tên gói, thời hạn, giá và trạng thái.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `package_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã gói AI. |
| `package_name` | `VARCHAR(150)` | NOT NULL | Tên gói AI. |
| `description` | `TEXT` | NULL | Mô tả nội dung hoặc mục đích. |
| `duration_months` | `INT UNSIGNED` | NOT NULL | Thời hạn gói, tính bằng tháng. |
| `price` | `DECIMAL(12,2)` | NOT NULL | Giá tiền của gói hoặc giao dịch. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'ACTIVE' | Trạng thái gói AI, ví dụ ACTIVE/INACTIVE. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

### `ai_package_limits` — Hạn mức gói AI
Cấu hình hạn mức của từng chức năng AI trong mỗi gói, gồm số lượng, đơn vị tính và chu kỳ làm mới.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `limit_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã cấu hình hạn mức. |
| `package_id` | `INT UNSIGNED` | FK → `ai_packages.package_id`, NOT NULL | Mã gói AI. |
| `feature_code` | `VARCHAR(50)` | NOT NULL | Mã chức năng AI được cấp hạn mức. |
| `quota_amount` | `DECIMAL(12,2)` | NOT NULL | Số lượng hạn mức được cấp hoặc tiêu thụ. |
| `quota_unit` | `VARCHAR(20)` | NOT NULL | Đơn vị hạn mức, ví dụ REQUESTS, TOKENS, MINUTES. |
| `reset_period` | `VARCHAR(30)` | NOT NULL, DEFAULT 'MONTHLY' | Chu kỳ làm mới hạn mức. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |

**Ràng buộc UNIQUE:** (`package_id`, `feature_code`).

### `ai_subscriptions` — Đăng ký gói AI
Lưu gói AI mà một người dùng đã đăng ký, thời gian bắt đầu/kết thúc và trạng thái đăng ký.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `subscription_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã đăng ký gói AI. |
| `user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `package_id` | `INT UNSIGNED` | FK → `ai_packages.package_id`, NOT NULL | Mã gói AI. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'PENDING_PAYMENT' | Trạng thái đăng ký: PENDING_PAYMENT, SCHEDULED, ACTIVE, EXPIRED hoặc CANCELLED. |
| `starts_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm gói bắt đầu có hiệu lực. |
| `ends_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm gói hết hiệu lực. |
| `cancelled_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm hủy gói. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

### `ai_usage_logs` — Nhật ký sử dụng AI
Ghi lại từng yêu cầu sử dụng AI, chức năng được dùng, lượng quota tiêu thụ và kết quả thành công/thất bại.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `usage_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã nhật ký sử dụng AI. |
| `subscription_id` | `INT UNSIGNED` | FK → `ai_subscriptions.subscription_id`, NOT NULL | Mã đăng ký gói AI. |
| `feature_code` | `VARCHAR(50)` | NOT NULL | Mã chức năng AI được cấp hạn mức. |
| `quantity_used` | `DECIMAL(12,2)` | NOT NULL, DEFAULT '0.00' | Lượng hạn mức tiêu thụ trong yêu cầu. |
| `quota_unit` | `VARCHAR(20)` | NOT NULL | Đơn vị hạn mức, ví dụ REQUESTS, TOKENS, MINUTES. |
| `request_status` | `VARCHAR(30)` | NOT NULL | Trạng thái yêu cầu AI, ví dụ SUCCESS hoặc FAILED. |
| `request_key` | `VARCHAR(150)` | NULL, DEFAULT NULL | Khóa nhận diện yêu cầu để tránh ghi nhận trùng. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |

**Ràng buộc UNIQUE:** (`request_key`).

### `payments` — Thanh toán
Lưu từng giao dịch thanh toán cho một đăng ký gói AI, số tiền, cổng thanh toán và trạng thái giao dịch.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `payment_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã giao dịch thanh toán. |
| `subscription_id` | `INT UNSIGNED` | FK → `ai_subscriptions.subscription_id`, NOT NULL | Mã đăng ký gói AI. |
| `amount` | `DECIMAL(12,2)` | NOT NULL | Số tiền thanh toán thực tế. |
| `currency_code` | `CHAR(3)` | NOT NULL, DEFAULT 'VND' | Mã tiền tệ, ví dụ VND. |
| `payment_method` | `VARCHAR(50)` | NOT NULL | Phương thức thanh toán. |
| `payment_gateway` | `VARCHAR(100)` | NOT NULL | Tên cổng thanh toán. |
| `gateway_transaction_id` | `VARCHAR(150)` | NULL, DEFAULT NULL | Mã giao dịch do cổng thanh toán cung cấp. |
| `idempotency_key` | `VARCHAR(150)` | NOT NULL | Khóa chống xử lý giao dịch trùng lặp. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'PENDING' | Trạng thái giao dịch: PENDING, SUCCESS, FAILED hoặc REFUNDED. |
| `paid_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm thanh toán thành công. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |

**Ràng buộc UNIQUE:** (`idempotency_key`); (`gateway_transaction_id`).

## Nhóm 7 – Phản hồi và hệ thống

### `feedback` — Phản hồi
Lưu góp ý, báo lỗi và phản hồi của người dùng cùng trạng thái, người xử lý và câu trả lời của Admin.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `feedback_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã phản hồi. |
| `user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `feedback_type` | `VARCHAR(50)` | NOT NULL | Loại phản hồi, ví dụ báo lỗi hoặc góp ý. |
| `subject` | `VARCHAR(200)` | NOT NULL | Tiêu đề phản hồi. |
| `content` | `TEXT` | NOT NULL | Nội dung phản hồi. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'PENDING' | Trạng thái phản hồi: PENDING, PROCESSING, RESOLVED hoặc REJECTED. |
| `admin_response` | `TEXT` | NULL | Nội dung phản hồi của Admin. |
| `handled_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người phụ trách xử lý phản hồi. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `updated_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm cập nhật bản ghi gần nhất. |
| `resolved_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm phản hồi được giải quyết. |

### `notifications` — Thông báo
Lưu thông báo gửi đến người dùng, loại thông báo, đối tượng liên quan và trạng thái đã đọc.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `notification_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã thông báo. |
| `user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `title` | `VARCHAR(200)` | NOT NULL | Tiêu đề thông báo. |
| `message` | `TEXT` | NOT NULL | Nội dung thông báo. |
| `notification_type` | `VARCHAR(50)` | NOT NULL | Loại thông báo. |
| `related_type` | `VARCHAR(50)` | NULL, DEFAULT NULL | Loại đối tượng mà thông báo liên quan. |
| `related_id` | `INT UNSIGNED` | NULL, DEFAULT NULL | ID bản ghi liên quan; phải xác định bảng mục tiêu qua related_type. |
| `is_read` | `TINYINT(1)` | NOT NULL, DEFAULT '0' | Cho biết thông báo đã được đọc hay chưa. |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm tạo bản ghi. |
| `read_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm người dùng đọc thông báo. |

### `account_deletion_requests` — Yêu cầu xóa tài khoản
Lưu yêu cầu người dùng muốn ngừng sử dụng tài khoản, quá trình Admin xét duyệt và thời điểm hoàn tất. Khi hoàn tất, hệ thống chuyển tài khoản sang trạng thái DEACTIVATED thay vì xóa lịch sử.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa tiếng Việt |
|---|---|---|---|
| `deletion_request_id` | `INT UNSIGNED` | PK, AUTO_INCREMENT, NOT NULL | Mã yêu cầu xóa tài khoản. |
| `user_id` | `INT UNSIGNED` | FK → `users.user_id`, NOT NULL | Mã tài khoản người dùng. |
| `reason` | `TEXT` | NULL | Lý do người dùng yêu cầu xóa tài khoản. |
| `status` | `VARCHAR(30)` | NOT NULL, DEFAULT 'PENDING' | Trạng thái hoạt động hoặc trạng thái nghiệp vụ của bản ghi. |
| `reviewed_by_user_id` | `INT UNSIGNED` | FK → `users.user_id`, NULL, DEFAULT NULL | Mã người xét duyệt/xử lý. |
| `admin_note` | `TEXT` | NULL | Ghi chú xử lý của Admin. |
| `requested_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm gửi yêu cầu đăng ký. |
| `reviewed_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm thực hiện lần ôn. |
| `completed_at` | `DATETIME` | NULL, DEFAULT NULL | Thời điểm hoàn tất xử lý yêu cầu. |

## Lưu ý khi lập trình

- Không đổi tên bảng/cột MySQL sang tiếng Việt; dùng tên tiếng Anh trong SQL, Python và Jinja2.
- Dùng tài liệu này để tra cứu ý nghĩa, còn `flashcard_lms.sql`/Database đang chạy là nguồn sự thật về kiểu dữ liệu và ràng buộc.
- Các liên kết đa hình như `notifications.related_type` + `notifications.related_id` không phải khóa ngoại vật lý. Backend phải xác thực loại đối tượng và ID.
- Một số quy tắc như chỉ một ngôn ngữ hiện tại, chỉ một gói AI ACTIVE, kiểm tra quyền Lecturer và tính hợp lệ của bài kiểm tra cần được bảo vệ trong Backend/transaction.
- Không import lại file dump SQL vào Database đang chạy; file dump có thể chứa `DROP TABLE IF EXISTS`.
