# Tạo, sửa, ẩn, xóa và xuất bản khóa học
from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import current_user

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

from .blueprint import lecturer_bp
from .common import (
    lecturer_required,
    visible_course_clause,
    get_course,
    get_languages,
    get_topics,
)



@lecturer_bp.get("/courses")
@lecturer_required
def courses():

    # ========================================
    # 1. LẤY ĐIỀU KIỆN TÌM KIẾM VÀ LỌC
    # ========================================

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    language_raw = request.args.get("language_id", "").strip()

    allowed_statuses = {
        "DRAFT",
        "PUBLISHED",
        "UNPUBLISHED",
    }

    if status not in allowed_statuses:
        status = ""

    try:
        language_id = int(language_raw) if language_raw else None
        if language_id is not None and language_id <= 0:
            language_id = None
    except ValueError:
        language_id = None

    # ========================================
    # 2. XÂY DỰNG ĐIỀU KIỆN SQL
    # ========================================

    where = [visible_course_clause()]

    params = {
        "user_id": current_user.user_id,
        "q": f"%{q}%",
    }

    if q:
        where.append("c.course_name LIKE :q")

    if status:
        where.append("c.status = :status")
        params["status"] = status

    if language_id is not None:
        where.append("c.language_id = :language_id")
        params["language_id"] = language_id

    # ========================================
    # 3. LẤY DANH SÁCH KHÓA HỌC
    # ========================================

    sql = f"""
        SELECT
            c.course_id,
            c.course_name,
            c.description,
            c.status,
            c.created_at,
            c.created_by_user_id,

            l.language_name,
            t.topic_name,

            (
                SELECT COUNT(*)
                FROM lessons le
                WHERE le.course_id = c.course_id
            ) AS lessons_count,

            (
                SELECT COUNT(*)
                FROM enrollments e
                WHERE e.course_id = c.course_id
                  AND e.status = 'APPROVED'
            ) AS learners_count,

            (
                SELECT COUNT(DISTINCT vi.item_id)
                FROM lessons le2
                JOIN lesson_vocabulary_sets lvs
                    ON lvs.lesson_id = le2.lesson_id
                JOIN vocabulary_sets vs
                    ON vs.set_id = lvs.set_id
                JOIN vocabulary_items vi
                    ON vi.set_id = vs.set_id
                WHERE le2.course_id = c.course_id
                  AND vs.status = 'ACTIVE'
                  AND vi.status = 'ACTIVE'
            ) AS flashcards_count,

            CASE
                WHEN c.created_by_user_id = :user_id THEN 1

                WHEN EXISTS (
                    SELECT 1
                    FROM course_lecturers cl
                    WHERE cl.course_id = c.course_id
                      AND cl.lecturer_user_id = :user_id
                      AND cl.permission = 'EDIT'
                ) THEN 1

                ELSE 0
            END AS can_edit

        FROM courses c

        JOIN languages l
            ON l.language_id = c.language_id

        LEFT JOIN topics t
            ON t.topic_id = c.topic_id
           AND t.language_id = c.language_id

        WHERE {" AND ".join(where)}

        ORDER BY c.created_at DESC
    """

    rows = db.session.execute(
        text(sql),
        params
    ).mappings().all()

    # ========================================
    # 4. THỐNG KÊ TẤT CẢ KHÓA HỌC
    # ========================================

    summary = db.session.execute(
        text(
            f"""
            SELECT
                COUNT(*) AS total_count,

                COALESCE(
                    SUM(c.status = 'PUBLISHED'), 0
                ) AS published_count,

                COALESCE(
                    SUM(c.status = 'DRAFT'), 0
                ) AS draft_count,

                COALESCE(
                    SUM(c.status = 'UNPUBLISHED'), 0
                ) AS unpublished_count

            FROM courses c

            WHERE {visible_course_clause()}
            """
        ),
        {"user_id": current_user.user_id},
    ).mappings().first()

    # ========================================
    # 5. TRẢ DỮ LIỆU CHO GIAO DIỆN
    # ========================================

    return render_template(
        "lecturer/courses.html",

        courses=[dict(row) for row in rows],

        summary=dict(summary or {}),

        languages=get_languages(),

        q=q,

        selected_status=status,

        selected_language=(
            str(language_id)
            if language_id is not None
            else ""
        ),
    )


def validate_course_form():
    course_name = request.form.get("course_name", "").strip()
    description = request.form.get("description", "").strip() or None
    language_raw = request.form.get("language_id", "").strip()
    topic_raw = request.form.get("topic_id", "").strip()

    if not course_name:
        return None, "Vui lòng nhập tên khóa học."
    if len(course_name) > 200:
        return None, "Tên khóa học không được vượt quá 200 ký tự."
    try:
        language_id = int(language_raw)
    except ValueError:
        return None, "Vui lòng chọn ngôn ngữ hợp lệ."

    language_exists = db.session.execute(
        text("SELECT COUNT(*) FROM languages WHERE language_id=:id AND status='ACTIVE'"),
        {"id": language_id},
    ).scalar()
    if not language_exists:
        return None, "Ngôn ngữ đã chọn không tồn tại hoặc không hoạt động."

    topic_id = None
    if topic_raw:
        try:
            topic_id = int(topic_raw)
        except ValueError:
            return None, "Chủ đề không hợp lệ."
        topic_exists = db.session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM topics
                WHERE topic_id = :topic_id
                  AND language_id = :language_id
                  AND status = 'ACTIVE'
                """
            ),
            {"topic_id": topic_id, "language_id": language_id},
        ).scalar()
        if not topic_exists:
            return None, "Chủ đề phải thuộc ngôn ngữ đã chọn."

    return {
        "course_name": course_name,
        "description": description,
        "language_id": language_id,
        "topic_id": topic_id,
    }, None


# ========================================
# TẠO KHÓA HỌC
# ========================================
@lecturer_bp.route("/courses/create", methods=["GET", "POST"])
@lecturer_required
def create_course():
    if request.method == "POST":
        data, error = validate_course_form()
        if error:
            flash(error, "danger")
        else:
            db.session.execute(
                text(
                    """
                    INSERT INTO courses
                        (course_name, description, language_id, topic_id,
                         created_by_user_id, status)
                    VALUES
                        (:course_name, :description, :language_id, :topic_id,
                         :user_id, 'DRAFT')
                    """
                ),
                {**data, "user_id": current_user.user_id},
            )
            db.session.commit()
            flash("Đã tạo khóa học ở trạng thái Nháp.", "success")
            return redirect(url_for("lecturer.courses"))

    selected_language = request.form.get("language_id", "")
    return render_template(
        "lecturer/course_form.html",
        page_title="Tạo khóa học",
        course=None,
        languages=get_languages(),
        topics=get_topics(selected_language if selected_language else None),
    )


@lecturer_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@lecturer_required
def edit_course(course_id):
    course = get_course(course_id, require_edit=True)

    if request.method == "POST":
        data, error = validate_course_form()
        if error:
            flash(error, "danger")
        else:
            db.session.execute(
                text(
                    """
                    UPDATE courses
                    SET course_name=:course_name,
                        description=:description,
                        language_id=:language_id,
                        topic_id=:topic_id
                    WHERE course_id=:course_id
                    """
                ),
                {**data, "course_id": course_id},
            )
            db.session.commit()
            flash("Đã cập nhật khóa học.", "success")
            return redirect(url_for("lecturer.courses"))

    return render_template(
        "lecturer/course_form.html",
        page_title="Chỉnh sửa khóa học",
        course=course,
        languages=get_languages(),
        topics=get_topics(course["language_id"]),
    )


@lecturer_bp.post("/courses/<int:course_id>/publish")
@lecturer_required
def publish_course(course_id):
    course = get_course(course_id, require_edit=True)

    valid_lessons = db.session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM lessons le
            WHERE le.course_id = :course_id
              AND (
                    (le.theory_content IS NOT NULL AND TRIM(le.theory_content) <> '')
                    OR EXISTS (
                        SELECT 1
                        FROM lesson_vocabulary_sets lvs
                        JOIN vocabulary_sets vs ON vs.set_id = lvs.set_id
                        WHERE lvs.lesson_id = le.lesson_id
                          AND vs.status = 'ACTIVE'
                    )
              )
            """
        ),
        {"course_id": course_id},
    ).scalar()

    if not valid_lessons:
        flash("Chưa thể xuất bản: khóa học cần ít nhất một bài học có lý thuyết hoặc Flashcard hợp lệ.", "warning")
        return redirect(url_for("lecturer.course_lessons", course_id=course_id))

    db.session.execute(
        text("UPDATE courses SET status='PUBLISHED' WHERE course_id=:course_id"),
        {"course_id": course_id},
    )
    db.session.commit()
    flash("Khóa học đã được xuất bản.", "success")
    return redirect(url_for("lecturer.courses"))


# ========================================
# ẨN KHÓA HỌC
# ========================================
@lecturer_bp.post("/courses/<int:course_id>/hide")
@lecturer_required
def hide_course(course_id):
    # Bước 1: Kiểm tra khóa học và quyền chỉnh sửa
    course = get_course(course_id, require_edit=True)

    # Bước 2: Chỉ cho phép ẩn khóa học đã xuất bản
    if course["status"] != "PUBLISHED":
        flash(
            "Chỉ có thể ẩn khóa học đã xuất bản.",
            "warning"
        )
        return redirect(url_for("lecturer.courses"))

    try:
        # Bước 3: Chuyển trạng thái sang UNPUBLISHED
        result = db.session.execute(
            text("""
                UPDATE courses
                SET status = 'UNPUBLISHED'
                WHERE course_id = :course_id
                  AND status = 'PUBLISHED'
            """),
            {"course_id": course_id}
        )

        if result.rowcount != 1:
            db.session.rollback()
            flash(
                "Trạng thái khóa học đã thay đổi. Vui lòng tải lại trang.",
                "warning"
            )
            return redirect(url_for("lecturer.courses"))

        # Bước 4: Lưu thay đổi
        db.session.commit()

        flash(
            "Đã ẩn khóa học thành công.",
            "success"
        )

    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "Không thể ẩn khóa học do lỗi cơ sở dữ liệu.",
            "danger"
        )

    return redirect(url_for("lecturer.courses"))


# ========================================
# XÓA KHÓA HỌC (BẢN NHÁP)
# ========================================
@lecturer_bp.post("/courses/<int:course_id>/delete")
@lecturer_required
def delete_course(course_id):
    # Bước 1: Kiểm tra quyền truy cập
    course = get_course(course_id, require_edit=True)

    # Bước 2: Không cho xóa trực tiếp khóa học đang xuất bản
    if course["status"] == "PUBLISHED":
        flash(
            "Vui lòng ẩn khóa học trước khi xóa.",
            "warning"
        )
        return redirect(url_for("lecturer.courses"))

    # Bước 3: Chỉ cho phép xóa bản nháp hoặc khóa học đã ẩn
    if course["status"] not in {"DRAFT", "UNPUBLISHED"}:
        flash(
            "Trạng thái khóa học không hợp lệ để xóa.",
            "warning"
        )
        return redirect(url_for("lecturer.courses"))

    try:
        # Bước 4: Kiểm tra dữ liệu liên quan
        dependencies = db.session.execute(
            text("""
                SELECT
                    (
                        SELECT COUNT(*)
                        FROM lessons
                        WHERE course_id = :course_id
                    ) AS lessons_count,

                    (
                        SELECT COUNT(*)
                        FROM enrollments
                        WHERE course_id = :course_id
                    ) AS enrollments_count,

                    (
                        SELECT COUNT(*)
                        FROM assessments
                        WHERE course_id = :course_id
                    ) AS assessments_count,

                    (
                        SELECT COUNT(*)
                        FROM course_lecturers
                        WHERE course_id = :course_id
                    ) AS lecturers_count
            """),
            {"course_id": course_id}
        ).mappings().first()

        # Bước 5: Tổng hợp những dữ liệu đang liên kết
        related_data = []

        if dependencies["lessons_count"] > 0:
            related_data.append(
                f'{dependencies["lessons_count"]} bài học'
            )

        if dependencies["enrollments_count"] > 0:
            related_data.append(
                f'{dependencies["enrollments_count"]} yêu cầu đăng ký'
            )

        if dependencies["assessments_count"] > 0:
            related_data.append(
                f'{dependencies["assessments_count"]} bài kiểm tra'
            )

        if dependencies["lecturers_count"] > 0:
            related_data.append(
                f'{dependencies["lecturers_count"]} giảng viên được phân công'
            )

        # Bước 6: Nếu có dữ liệu liên quan thì từ chối xóa
        if related_data:
            details = ", ".join(related_data)

            flash(
                f"Không thể xóa khóa học vì còn dữ liệu liên quan: {details}.",
                "warning"
            )

            return redirect(url_for("lecturer.courses"))

        # Bước 7: Chỉ xóa khi không có dữ liệu phụ thuộc
        db.session.execute(
            text("""
                DELETE FROM courses
                WHERE course_id = :course_id
            """),
            {"course_id": course_id}
        )

        db.session.commit()

        flash(
            "Đã xóa khóa học thành công.",
            "success"
        )

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "Không thể xóa khóa học. Dữ liệu có thể đang được sử dụng.",
            "danger"
        )

    return redirect(url_for("lecturer.courses"))
