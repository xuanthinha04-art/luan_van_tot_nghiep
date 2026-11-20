# Quản lý yêu cầu tham gia khóa học và học viên

from datetime import datetime

from flask import (
    abort,
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
    visible_course_clause,
    get_course,
)
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
