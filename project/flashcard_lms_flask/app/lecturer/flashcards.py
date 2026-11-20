# Tạo, xem và quản lý bộ Flashcard
# Quản lý bộ Flashcard trong khóa học
from flask import (
    abort,
    current_app,
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
from .common import lecturer_required, get_course



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



@lecturer_bp.get("/flashcard-sets/<int:set_id>")
@lecturer_required
def view_flashcard_set(set_id):

# ========================================
# 1. KIỂM TRA QUYỀN XEM BỘ FLASHCARD
# ========================================

    set_row = db.session.execute(
        text("""
            SELECT
                vs.set_id,
                vs.set_name,
                vs.description,
                vs.set_type,
                vs.language_id,
                vs.topic_id,
                vs.owner_user_id,
                vs.created_by_user_id,
                vs.status,
                vs.created_at,

                l.language_name,
                t.topic_name,

                (
                    SELECT COUNT(*)
                    FROM vocabulary_items vi
                    WHERE vi.set_id = vs.set_id
                ) AS total_items,

                (
                    SELECT COUNT(*)
                    FROM vocabulary_items vi
                    WHERE vi.set_id = vs.set_id
                      AND vi.status = 'ACTIVE'
                ) AS active_items,

                (
                    SELECT COUNT(DISTINCT lvs.lesson_id)
                    FROM lesson_vocabulary_sets lvs
                    WHERE lvs.set_id = vs.set_id
                ) AS linked_lessons_count

            FROM vocabulary_sets vs

            JOIN languages l
                ON l.language_id = vs.language_id

            LEFT JOIN topics t
                ON t.topic_id = vs.topic_id
               AND t.language_id = vs.language_id

            WHERE vs.set_id = :set_id

              AND (
                    vs.set_type = 'COMMON'
                    OR vs.owner_user_id = :user_id
                    OR vs.created_by_user_id = :user_id
              )

            LIMIT 1
        """),
        {
            "set_id": set_id,
            "user_id": current_user.user_id
        }
    ).mappings().first()

    # Không tồn tại hoặc không được phép xem
    if not set_row:
        abort(404)

    flashcard_set = dict(set_row)

# ========================================
# 2. XÁC ĐỊNH QUYỀN CHỈNH SỬA
# ========================================

    can_edit = (
        flashcard_set["set_type"] != "COMMON"
        and (
            flashcard_set["owner_user_id"] == current_user.user_id
            or flashcard_set["created_by_user_id"] == current_user.user_id
        )
    )

# ========================================
# 3. LẤY DANH SÁCH TỪ VỰNG
# ========================================

    item_rows = db.session.execute(
        text("""
            SELECT
                item_id,
                set_id,
                term,
                meaning,
                example,
                image_url,
                display_order,
                status

            FROM vocabulary_items

            WHERE set_id = :set_id

            ORDER BY display_order ASC, item_id ASC
        """),
        {"set_id": set_id}
    ).mappings().all()

    items = [
        dict(row)
        for row in item_rows
    ]

# ========================================
# 4. TRẢ DỮ LIỆU CHO GIAO DIỆN
# ========================================

    return render_template(
        "lecturer/flashcard_set_detail.html",

        flashcard_set=flashcard_set,

        items=items,

        can_edit=can_edit
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
