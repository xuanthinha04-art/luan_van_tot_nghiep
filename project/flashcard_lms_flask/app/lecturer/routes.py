from datetime import datetime

from flask import (
    Blueprint, abort, current_app, flash,
    redirect, render_template, request, url_for
)
from flask_login import current_user, login_required
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

lecturer_bp = Blueprint("lecturer", __name__, url_prefix="/lecturer")


def lecturer_required(view):
    from functools import wraps

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if getattr(current_user, "role_name", None) != "LECTURER":
            abort(403)
        if getattr(current_user, "account_status", None) != "ACTIVE":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def visible_course_clause():
    return """
        (
            c.created_by_user_id = :user_id
            OR EXISTS (
                SELECT 1
                FROM course_lecturers cl
                WHERE cl.course_id = c.course_id
                  AND cl.lecturer_user_id = :user_id
            )
        )
    """


def get_course(course_id: int, require_edit: bool = False):
    row = db.session.execute(
        text(
            f"""
            SELECT c.course_id, c.course_name, c.description, c.language_id,
                   c.topic_id, c.created_by_user_id, c.status, c.created_at,
                   l.language_name, t.topic_name
            FROM courses c
            JOIN languages l ON l.language_id = c.language_id
            LEFT JOIN topics t
                   ON t.topic_id = c.topic_id AND t.language_id = c.language_id
            WHERE c.course_id = :course_id
              AND {visible_course_clause()}
            LIMIT 1
            """
        ),
        {"course_id": course_id, "user_id": current_user.user_id},
    ).mappings().first()

    if not row:
        abort(404)

    course = dict(row)
    if require_edit and course["created_by_user_id"] != current_user.user_id:
        permission = db.session.execute(
            text(
                """
                SELECT permission
                FROM course_lecturers
                WHERE course_id = :course_id
                  AND lecturer_user_id = :user_id
                LIMIT 1
                """
            ),
            {"course_id": course_id, "user_id": current_user.user_id},
        ).scalar()
        if permission != "EDIT":
            abort(403)

    return course


def get_languages():
    rows = db.session.execute(
        text(
            """
            SELECT language_id, language_name
            FROM languages
            WHERE status = 'ACTIVE'
            ORDER BY language_name
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def get_topics(language_id=None):
    if language_id:
        rows = db.session.execute(
            text(
                """
                SELECT topic_id, topic_name, language_id
                FROM topics
                WHERE status = 'ACTIVE' AND language_id = :language_id
                ORDER BY topic_name
                """
            ),
            {"language_id": language_id},
        ).mappings().all()
    else:
        rows = db.session.execute(
            text(
                """
                SELECT topic_id, topic_name, language_id
                FROM topics
                WHERE status = 'ACTIVE'
                ORDER BY language_id, topic_name
                """
            )
        ).mappings().all()
    return [dict(row) for row in rows]


@lecturer_bp.get("/dashboard")
@lecturer_required
def dashboard():
    user_id = current_user.user_id
    clause = visible_course_clause()

    stats = db.session.execute(
        text(
            f"""
            SELECT
              (
                SELECT COUNT(*)
                FROM courses c
                WHERE {clause}
              ) AS course_count,
              (
                SELECT COUNT(*)
                FROM lessons le
                JOIN courses c ON c.course_id = le.course_id
                WHERE {clause}
              ) AS lesson_count,
              (
                SELECT COUNT(*)
                FROM enrollments e
                JOIN courses c ON c.course_id = e.course_id
                WHERE {clause} AND e.status = 'APPROVED'
              ) AS learner_count,
              (
                SELECT COUNT(*)
                FROM enrollments e
                JOIN courses c ON c.course_id = e.course_id
                WHERE {clause} AND e.status = 'PENDING'
              ) AS pending_count
            """
        ),
        {"user_id": user_id},
    ).mappings().first()

    courses = db.session.execute(
        text(
            f"""
            SELECT c.course_id, c.course_name, c.status, c.created_at,
                   l.language_name, t.topic_name,
                   (SELECT COUNT(*) FROM lessons le
                    WHERE le.course_id = c.course_id) AS lessons_count,
                   (SELECT COUNT(*) FROM enrollments e
                    WHERE e.course_id = c.course_id
                      AND e.status = 'APPROVED') AS learners_count
            FROM courses c
            JOIN languages l ON l.language_id = c.language_id
            LEFT JOIN topics t
                   ON t.topic_id = c.topic_id AND t.language_id = c.language_id
            WHERE {clause}
            ORDER BY c.created_at DESC
            LIMIT 5
            """
        ),
        {"user_id": user_id},
    ).mappings().all()

    pending = db.session.execute(
        text(
            f"""
            SELECT e.enrollment_id, e.requested_at,
                   u.full_name AS learner_name, u.email,
                   c.course_name, c.course_id
            FROM enrollments e
            JOIN users u ON u.user_id = e.learner_user_id
            JOIN courses c ON c.course_id = e.course_id
            WHERE {clause} AND e.status = 'PENDING'
            ORDER BY e.requested_at DESC
            LIMIT 5
            """
        ),
        {"user_id": user_id},
    ).mappings().all()

    return render_template(
        "lecturer/dashboard.html",
        stats=dict(stats or {}),
        courses=[dict(row) for row in courses],
        pending=[dict(row) for row in pending],
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



@lecturer_bp.get("/courses/<int:course_id>/lessons")
@lecturer_required
def course_lessons(course_id):

    # ========================================
    # 1. KIỂM TRA KHÓA HỌC
    # ========================================

    course = get_course(course_id)
    # Kiểm tra quyền chỉnh sửa khóa học
    can_edit_course = (
        course["created_by_user_id"] == current_user.user_id
    )

    if not can_edit_course:
        permission = db.session.execute(
            text("""
                SELECT permission
                FROM course_lecturers
                WHERE course_id = :course_id
                AND lecturer_user_id = :user_id
                LIMIT 1
            """),
            {
                "course_id": course_id,
                "user_id": current_user.user_id
            }
        ).scalar()

        can_edit_course = permission == "EDIT"

    params = {
        "course_id": course_id
    }

    # ========================================
    # 2. LẤY DANH SÁCH BÀI HỌC
    # ========================================

    lessons_rows = db.session.execute(
        text(
            """
            SELECT
                le.lesson_id,
                le.course_id,
                le.lesson_name,
                le.description,
                le.theory_content,
                le.lesson_order,
                le.status,

                (
                    SELECT COUNT(DISTINCT lvs.lesson_vocabulary_set_id)
                    FROM lesson_vocabulary_sets lvs
                    WHERE lvs.lesson_id = le.lesson_id
                ) AS flashcard_sets_count,

                (
                    SELECT COUNT(DISTINCT vi.item_id)
                    FROM lesson_vocabulary_sets lvs
                    JOIN vocabulary_sets vs
                        ON vs.set_id = lvs.set_id
                    JOIN vocabulary_items vi
                        ON vi.set_id = vs.set_id
                    WHERE lvs.lesson_id = le.lesson_id
                      AND vs.status = 'ACTIVE'
                      AND vi.status = 'ACTIVE'
                ) AS vocabulary_count

            FROM lessons le

            WHERE le.course_id = :course_id

            ORDER BY le.lesson_order ASC, le.lesson_id ASC
            """
        ),
        params
    ).mappings().all()

    lessons = [
        dict(row)
        for row in lessons_rows
    ]

    # ========================================
    # 3. LẤY CÁC BỘ FLASHCARD ĐÃ GẮN
    # ========================================

    attached_rows = db.session.execute(
        text(
            """
            SELECT
                lvs.lesson_id,
                lvs.set_id,
                lvs.display_order,

                vs.set_name,
                vs.set_type,
                vs.status AS set_status,

                (
                    SELECT COUNT(*)
                    FROM vocabulary_items vi
                    WHERE vi.set_id = vs.set_id
                      AND vi.status = 'ACTIVE'
                ) AS vocabulary_count

            FROM lesson_vocabulary_sets lvs

            JOIN lessons le
                ON le.lesson_id = lvs.lesson_id

            JOIN vocabulary_sets vs
                ON vs.set_id = lvs.set_id

            WHERE le.course_id = :course_id

            ORDER BY
                lvs.lesson_id,
                lvs.display_order,
                vs.set_name
            """
        ),
        params
    ).mappings().all()

    # Gom các bộ Flashcard theo từng bài học
    attached_sets_by_lesson = {}

    for row in attached_rows:

        lesson_id = row["lesson_id"]

        if lesson_id not in attached_sets_by_lesson:
            attached_sets_by_lesson[lesson_id] = []

        attached_sets_by_lesson[lesson_id].append(
            dict(row)
        )

    # Gắn danh sách Flashcard vào từng bài học
    for lesson in lessons:

        lesson["vocabulary_sets"] = (
            attached_sets_by_lesson.get(
                lesson["lesson_id"],
                []
            )
        )

    # ========================================
    # 4. THỐNG KÊ TỔNG QUAN KHÓA HỌC
    # ========================================

    summary_row = db.session.execute(
        text(
            """
            SELECT

                COUNT(DISTINCT le.lesson_id)
                    AS total_lessons,

                COUNT(DISTINCT lvs.lesson_vocabulary_set_id)
                    AS total_flashcard_sets,

                COUNT(
                    DISTINCT CASE
                        WHEN vs.status = 'ACTIVE'
                         AND vi.status = 'ACTIVE'
                        THEN vi.item_id
                    END
                ) AS total_vocabulary

            FROM lessons le

            LEFT JOIN lesson_vocabulary_sets lvs
                ON lvs.lesson_id = le.lesson_id

            LEFT JOIN vocabulary_sets vs
                ON vs.set_id = lvs.set_id

            LEFT JOIN vocabulary_items vi
                ON vi.set_id = vs.set_id

            WHERE le.course_id = :course_id
            """
        ),
        params
    ).mappings().first()

    summary = dict(summary_row or {})

    # ========================================
    # 5. LẤY CÁC BỘ FLASHCARD CÓ THỂ GẮN
    # ========================================

    available_sets_rows = db.session.execute(
        text(
            """
            SELECT
                set_id,
                set_name,
                set_type

            FROM vocabulary_sets

            WHERE language_id = :language_id
              AND status = 'ACTIVE'
              AND (
                    set_type = 'COMMON'
                    OR owner_user_id = :user_id
                    OR created_by_user_id = :user_id
              )

            ORDER BY set_name
            """
        ),
        {
            "language_id": course["language_id"],
            "user_id": current_user.user_id
        }
    ).mappings().all()

    vocabulary_sets = [
        dict(row)
        for row in available_sets_rows
    ]

    # ========================================
    # 6. TRẢ DỮ LIỆU VỀ GIAO DIỆN
    # ========================================

    return render_template(
    "lecturer/lessons.html",
    course=course,
    lessons=lessons,
    summary=summary,
    vocabulary_sets=vocabulary_sets,
    can_edit_course=can_edit_course
)



@lecturer_bp.route("/courses/<int:course_id>/lessons/create", methods=["POST"])
@lecturer_required
def create_lesson(course_id):
    get_course(course_id, require_edit=True)
    lesson_name = request.form.get("lesson_name", "").strip()
    description = request.form.get("description", "").strip() or None
    theory_content = request.form.get("theory_content", "").strip() or None

    if not lesson_name or len(lesson_name) > 200:
        flash("Tên bài học là bắt buộc và không vượt quá 200 ký tự.", "danger")
        return redirect(url_for("lecturer.course_lessons", course_id=course_id))

    next_order = db.session.execute(
        text("SELECT COALESCE(MAX(lesson_order), 0) + 1 FROM lessons WHERE course_id=:course_id"),
        {"course_id": course_id},
    ).scalar()

    db.session.execute(
        text(
            """
            INSERT INTO lessons
                (course_id, lesson_name, description, theory_content, lesson_order, status)
            VALUES
                (:course_id, :lesson_name, :description, :theory_content, :lesson_order, 'DRAFT')
            """
        ),
        {
            "course_id": course_id,
            "lesson_name": lesson_name,
            "description": description,
            "theory_content": theory_content,
            "lesson_order": next_order,
        },
    )
    db.session.commit()
    flash("Đã thêm bài học.", "success")
    return redirect(url_for("lecturer.course_lessons", course_id=course_id))


@lecturer_bp.post("/lessons/<int:lesson_id>/attach-set")
@lecturer_required
def attach_vocabulary_set(lesson_id):
    row = db.session.execute(
        text(
            """
            SELECT le.lesson_id, le.course_id, c.language_id
            FROM lessons le
            JOIN courses c ON c.course_id = le.course_id
            WHERE le.lesson_id = :lesson_id
            LIMIT 1
            """
        ),
        {"lesson_id": lesson_id},
    ).mappings().first()

    if not row:
        abort(404)

    course = get_course(row["course_id"], require_edit=True)
    try:
        set_id = int(request.form.get("set_id", ""))
    except ValueError:
        flash("Vui lòng chọn bộ Flashcard.", "danger")
        return redirect(url_for("lecturer.course_lessons", course_id=row["course_id"]))

    allowed = db.session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM vocabulary_sets
            WHERE set_id=:set_id
              AND language_id=:language_id
              AND status='ACTIVE'
              AND (
                    set_type='COMMON'
                    OR owner_user_id=:user_id
                    OR created_by_user_id=:user_id
              )
            """
        ),
        {
            "set_id": set_id,
            "language_id": course["language_id"],
            "user_id": current_user.user_id,
        },
    ).scalar()

    if not allowed:
        flash("Bộ Flashcard không hợp lệ hoặc bạn không có quyền sử dụng.", "danger")
        return redirect(url_for("lecturer.course_lessons", course_id=row["course_id"]))

    next_order = db.session.execute(
        text(
            """
            SELECT COALESCE(MAX(display_order), 0) + 1
            FROM lesson_vocabulary_sets
            WHERE lesson_id=:lesson_id
            """
        ),
        {"lesson_id": lesson_id},
    ).scalar()

    try:
        db.session.execute(
            text(
                """
                INSERT INTO lesson_vocabulary_sets
                    (lesson_id, set_id, display_order)
                VALUES (:lesson_id, :set_id, :display_order)
                """
            ),
            {"lesson_id": lesson_id, "set_id": set_id, "display_order": next_order},
        )
        db.session.commit()
        flash("Đã thêm bộ Flashcard vào bài học.", "success")
    except Exception:
        db.session.rollback()
        flash("Bộ Flashcard này có thể đã được thêm vào bài học.", "warning")

    return redirect(url_for("lecturer.course_lessons", course_id=row["course_id"]))



@lecturer_bp.post(
    "/lessons/<int:lesson_id>/flashcard-sets/<int:set_id>/remove"
)
@lecturer_required
def detach_vocabulary_set(lesson_id, set_id):

    # 1. Kiểm tra bài học tồn tại và lấy khóa học sở hữu
    lesson = db.session.execute(
        text("""
            SELECT lesson_id, course_id
            FROM lessons
            WHERE lesson_id = :lesson_id
            LIMIT 1
        """),
        {"lesson_id": lesson_id}
    ).mappings().first()

    if not lesson:
        abort(404)

    # 2. Kiểm tra quyền chỉnh sửa khóa học
    get_course(lesson["course_id"], require_edit=True)

    try:
        # 3. Chỉ xóa liên kết giữa bài học và bộ Flashcard
        result = db.session.execute(
            text("""
                DELETE FROM lesson_vocabulary_sets
                WHERE lesson_id = :lesson_id
                  AND set_id = :set_id
            """),
            {
                "lesson_id": lesson_id,
                "set_id": set_id
            }
        )

        if result.rowcount != 1:
            db.session.rollback()
            flash(
                "Bộ Flashcard không còn được gắn vào bài học.",
                "warning"
            )
        else:
            db.session.commit()
            flash(
                "Đã gỡ bộ Flashcard khỏi bài học.",
                "success"
            )

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "Không thể gỡ bộ Flashcard. Vui lòng thử lại.",
            "danger"
        )

    return redirect(
        url_for(
            "lecturer.course_lessons",
            course_id=lesson["course_id"]
        )
    )



@lecturer_bp.post(
    "/courses/<int:course_id>/lessons/<int:lesson_id>/flashcard-sets/create"
)
@lecturer_required
def create_and_attach_vocabulary_set(course_id, lesson_id):

    # ========================================
    # 1. KIỂM TRA QUYỀN KHÓA HỌC
    # ========================================

    course = get_course(course_id, require_edit=True)

    # Kiểm tra bài học có thuộc khóa học này không
    lesson_exists = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM lessons
            WHERE lesson_id = :lesson_id
              AND course_id = :course_id
        """),
        {
            "lesson_id": lesson_id,
            "course_id": course_id
        }
    ).scalar()

    if not lesson_exists:
        abort(404)

    # ========================================
    # 2. LẤY THÔNG TIN BỘ FLASHCARD
    # ========================================

    set_name = request.form.get("set_name", "").strip()

    description = (
        request.form.get("description", "").strip() or None
    )

    vocabulary_text = request.form.get(
        "vocabulary_entries", ""
    )

    if not set_name:
        flash("Vui lòng nhập tên bộ Flashcard.", "danger")
        return redirect(url_for(
            "lecturer.course_lessons",
            course_id=course_id
        ))

    if len(set_name) > 200:
        flash("Tên bộ Flashcard không được vượt quá 200 ký tự.", "danger")
        return redirect(url_for(
            "lecturer.course_lessons",
            course_id=course_id
        ))

    # ========================================
    # 3. PHÂN TÍCH DANH SÁCH TỪ VỰNG
    # ========================================

    vocabulary_items = []

    for line_number, raw_line in enumerate(
        vocabulary_text.splitlines(), start=1
    ):

        if not raw_line.strip():
            continue

        # Mỗi dòng gồm:
        # Từ vựng [TAB] Nghĩa [TAB] Ví dụ (không bắt buộc)

        columns = [
            value.strip()
            for value in raw_line.split("\t")
        ]

        if len(columns) not in (2, 3):
            flash(
                f"Dòng {line_number} không hợp lệ. "
                "Mỗi dòng cần có 2 hoặc 3 cột: "
                "Từ vựng, Nghĩa, Ví dụ.",
                "danger"
            )
            return redirect(url_for(
                "lecturer.course_lessons",
                course_id=course_id
            ))

        term = columns[0]
        meaning = columns[1]
        example = columns[2] if len(columns) == 3 else None

        if not term or not meaning:
            flash(
                f"Dòng {line_number} phải có cả từ vựng và nghĩa.",
                "danger"
            )
            return redirect(url_for(
                "lecturer.course_lessons",
                course_id=course_id
            ))

        if len(term) > 255:
            flash(
                f"Từ vựng ở dòng {line_number} vượt quá 255 ký tự.",
                "danger"
            )
            return redirect(url_for(
                "lecturer.course_lessons",
                course_id=course_id
            ))

        vocabulary_items.append({
            "term": term,
            "meaning": meaning,
            "example": example
        })

    if not vocabulary_items:
        flash("Vui lòng nhập ít nhất một từ vựng.", "danger")
        return redirect(url_for(
            "lecturer.course_lessons",
            course_id=course_id
        ))

    # ========================================
    # 4. TẠO BỘ FLASHCARD VÀ THÊM TỪ VỰNG
    # ========================================

    try:

        # Tạo bộ Flashcard thuộc quyền sở hữu giảng viên
        result = db.session.execute(
            text("""
                INSERT INTO vocabulary_sets (
                    set_name,
                    description,
                    set_type,
                    language_id,
                    topic_id,
                    owner_user_id,
                    created_by_user_id,
                    status
                )
                VALUES (
                    :set_name,
                    :description,
                    'LECTURER',
                    :language_id,
                    :topic_id,
                    :user_id,
                    :user_id,
                    'ACTIVE'
                )
            """),
            {
                "set_name": set_name,
                "description": description,
                "language_id": course["language_id"],
                "topic_id": course["topic_id"],
                "user_id": current_user.user_id
            }
        )

        new_set_id = result.lastrowid

        # Thêm từng từ vựng vào bộ vừa tạo
        for index, item in enumerate(vocabulary_items, start=1):

            db.session.execute(
                text("""
                    INSERT INTO vocabulary_items (
                        set_id,
                        term,
                        meaning,
                        example,
                        display_order,
                        status
                    )
                    VALUES (
                        :set_id,
                        :term,
                        :meaning,
                        :example,
                        :display_order,
                        'ACTIVE'
                    )
                """),
                {
                    "set_id": new_set_id,
                    "term": item["term"],
                    "meaning": item["meaning"],
                    "example": item["example"],
                    "display_order": index
                }
            )

        # ========================================
        # 5. GẮN BỘ FLASHCARD VÀO BÀI HỌC
        # ========================================

        next_order = db.session.execute(
            text("""
                SELECT COALESCE(MAX(display_order), 0) + 1
                FROM lesson_vocabulary_sets
                WHERE lesson_id = :lesson_id
            """),
            {"lesson_id": lesson_id}
        ).scalar()

        db.session.execute(
            text("""
                INSERT INTO lesson_vocabulary_sets (
                    lesson_id,
                    set_id,
                    display_order
                )
                VALUES (
                    :lesson_id,
                    :set_id,
                    :display_order
                )
            """),
            {
                "lesson_id": lesson_id,
                "set_id": new_set_id,
                "display_order": next_order
            }
        )

        # ========================================
        # 6. LƯU GIAO DỊCH
        # ========================================

        db.session.commit()

        flash(
            f"Đã tạo bộ Flashcard và thêm "
            f"{len(vocabulary_items)} từ vựng vào bài học.",
            "success"
        )

    except SQLAlchemyError:

        # Ghi lại lỗi SQL chi tiết vào Terminal
        current_app.logger.exception(
            "Loi khi tao va gan bo Flashcard"
        )

        # Hoàn tác toàn bộ giao dịch
        db.session.rollback()

        flash(
            "Không thể tạo bộ Flashcard. "
            "Vui lòng kiểm tra lỗi trong Terminal.",
            "danger"
        )

    return redirect(url_for(
        "lecturer.course_lessons",
        course_id=course_id
    ))



@lecturer_bp.get("/enrollments")
@lecturer_required
def enrollments():
    rows = db.session.execute(
        text(
            f"""
            SELECT e.enrollment_id, e.status, e.requested_at,
                   e.reviewed_at, e.rejection_reason,
                   u.full_name AS learner_name, u.email,
                   c.course_name, c.course_id
            FROM enrollments e
            JOIN users u ON u.user_id = e.learner_user_id
            JOIN courses c ON c.course_id = e.course_id
            WHERE {visible_course_clause()}
            ORDER BY
              CASE e.status WHEN 'PENDING' THEN 0 WHEN 'APPROVED' THEN 1 ELSE 2 END,
              e.requested_at DESC
            """
        ),
        {"user_id": current_user.user_id},
    ).mappings().all()
    return render_template("lecturer/enrollments.html", enrollments=[dict(row) for row in rows])


@lecturer_bp.post("/enrollments/<int:enrollment_id>/review")
@lecturer_required
def review_enrollment(enrollment_id):
    action = request.form.get("action", "").upper()
    reason = request.form.get("rejection_reason", "").strip() or None

    if action not in {"APPROVED", "REJECTED"}:
        flash("Thao tác duyệt không hợp lệ.", "danger")
        return redirect(url_for("lecturer.enrollments"))

    row = db.session.execute(
        text(
            """
            SELECT e.enrollment_id, e.status, e.course_id
            FROM enrollments e
            WHERE e.enrollment_id = :enrollment_id
            LIMIT 1
            """
        ),
        {"enrollment_id": enrollment_id},
    ).mappings().first()

    if not row:
        abort(404)

    get_course(row["course_id"], require_edit=True)

    if row["status"] != "PENDING":
        flash("Yêu cầu này đã được xử lý trước đó.", "warning")
        return redirect(url_for("lecturer.enrollments"))

    db.session.execute(
        text(
            """
            UPDATE enrollments
            SET status=:status,
                reviewed_by_user_id=:reviewer_id,
                reviewed_at=:reviewed_at,
                rejection_reason=:reason
            WHERE enrollment_id=:enrollment_id
              AND status='PENDING'
            """
        ),
        {
            "status": action,
            "reviewer_id": current_user.user_id,
            "reviewed_at": datetime.now(),
            "reason": reason if action == "REJECTED" else None,
            "enrollment_id": enrollment_id,
        },
    )
    db.session.commit()
    flash("Đã cập nhật yêu cầu tham gia khóa học.", "success")
    return redirect(url_for("lecturer.enrollments"))


@lecturer_bp.get("/students")
@lecturer_required
def students():
    rows = db.session.execute(
        text(
            f"""
            SELECT u.user_id, u.full_name, u.email,
                   c.course_name, e.requested_at AS enrolled_at
            FROM enrollments e
            JOIN users u ON u.user_id = e.learner_user_id
            JOIN courses c ON c.course_id = e.course_id
            WHERE {visible_course_clause()}
              AND e.status = 'APPROVED'
            ORDER BY e.requested_at DESC
            """
        ),
        {"user_id": current_user.user_id},
    ).mappings().all()
    return render_template("lecturer/students.html", students=[dict(row) for row in rows])
