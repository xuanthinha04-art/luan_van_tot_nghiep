# Các hàm dùng chung, kiểm tra quyền và truy vấn
from functools import wraps

from flask import abort
from flask_login import current_user, login_required
from sqlalchemy import text

from app.extensions import db


def lecturer_required(view):
    """Yêu cầu người dùng đăng nhập, có vai trò Lecturer và tài khoản đang hoạt động."""

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
    """Điều kiện xác định các khóa học Lecturer được phép xem."""

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
    """Lấy thông tin khóa học và kiểm tra quyền truy cập."""

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
    """Lấy danh sách ngôn ngữ đang hoạt động."""

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
    """Lấy danh sách chủ đề, có thể lọc theo ngôn ngữ."""

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