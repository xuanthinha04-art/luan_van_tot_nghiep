from datetime import datetime

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, url_for
)
from flask_login import current_user, login_required
from sqlalchemy import text

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


@lecturer_bp.get("/courses/<int:course_id>/lessons")
@lecturer_required
def course_lessons(course_id):
    course = get_course(course_id)
    lessons = db.session.execute(
        text(
            """
            SELECT le.lesson_id, le.lesson_name, le.description,
                   le.lesson_order, le.status, le.theory_content,
                   (SELECT COUNT(*)
                    FROM lesson_vocabulary_sets lvs
                    WHERE lvs.lesson_id = le.lesson_id) AS flashcard_sets_count
            FROM lessons le
            WHERE le.course_id = :course_id
            ORDER BY le.lesson_order
            """
        ),
        {"course_id": course_id},
    ).mappings().all()

    sets = db.session.execute(
        text(
            """
            SELECT set_id, set_name, set_type
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
        {"language_id": course["language_id"], "user_id": current_user.user_id},
    ).mappings().all()

    return render_template(
        "lecturer/lessons.html",
        course=course,
        lessons=[dict(row) for row in lessons],
        vocabulary_sets=[dict(row) for row in sets],
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
