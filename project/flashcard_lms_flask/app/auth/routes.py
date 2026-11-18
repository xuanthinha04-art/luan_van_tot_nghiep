from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import text
from werkzeug.security import check_password_hash

from app.extensions import db
from .models import AuthUser

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def load_auth_user(user_id: str):
    row = db.session.execute(
        text(
            """
            SELECT u.user_id, u.full_name, u.email, u.password_hash,
                   u.avatar_url, u.role_id, u.account_status, r.role_name
            FROM users AS u
            JOIN roles AS r ON r.role_id = u.role_id
            WHERE u.user_id = :user_id
            LIMIT 1
            """
        ),
        {"user_id": user_id},
    ).mappings().first()

    if not row:
        return None

    return AuthUser(
        user_id=row["user_id"],
        full_name=row["full_name"],
        email=row["email"],
        password_hash=row["password_hash"],
        avatar_url=row["avatar_url"],
        role_id=row["role_id"],
        role_name=row["role_name"],
        account_status=row["account_status"],
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role_name == "LECTURER":
            return redirect(url_for("lecturer.dashboard"))
        logout_user()
        flash("Tài khoản này không có quyền truy cập khu vực Giảng viên.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        row = db.session.execute(
            text(
                """
                SELECT u.user_id, u.full_name, u.email, u.password_hash,
                       u.avatar_url, u.role_id, u.account_status, r.role_name
                FROM users AS u
                JOIN roles AS r ON r.role_id = u.role_id
                WHERE u.email = :email
                LIMIT 1
                """
            ),
            {"email": email},
        ).mappings().first()

        if not row or not check_password_hash(row["password_hash"], password):
            flash("Email hoặc mật khẩu không chính xác.", "danger")
            return render_template("auth/login.html")

        if row["account_status"] != "ACTIVE":
            flash("Tài khoản hiện không ở trạng thái hoạt động.", "warning")
            return render_template("auth/login.html")

        if row["role_name"] != "LECTURER":
            flash("Tài khoản này chưa có quyền truy cập khu vực Giảng viên.", "warning")
            return render_template("auth/login.html")

        user = AuthUser(
            user_id=row["user_id"],
            full_name=row["full_name"],
            email=row["email"],
            password_hash=row["password_hash"],
            avatar_url=row["avatar_url"],
            role_id=row["role_id"],
            role_name=row["role_name"],
            account_status=row["account_status"],
        )
        login_user(user, remember=bool(request.form.get("remember")))
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)
        return redirect(url_for("lecturer.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("auth.login"))
