# Dashboard Giảng viên
from flask import render_template
from flask_login import current_user
from sqlalchemy import text

from app.extensions import db
from .blueprint import lecturer_bp
from .common import lecturer_required, visible_course_clause


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