# Quản lý bài học và gắn bộ Flashcard
from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import current_user

from sqlalchemy import text

from app.extensions import db

from .blueprint import lecturer_bp
from .common import (
    lecturer_required,
    get_course,
)
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
