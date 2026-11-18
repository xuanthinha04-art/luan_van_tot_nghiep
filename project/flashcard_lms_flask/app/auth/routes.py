from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import current_app
import re
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


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    # ========================================
    # 1. HIỂN THỊ TRANG ĐĂNG KÝ
    # ========================================

    if request.method == "GET":
        return render_template("auth/register.html")

    # ========================================
    # 2. LẤY DỮ LIỆU TỪ FORM
    # ========================================

    full_name = " ".join(
        request.form.get("full_name", "").split()
    )

    email = request.form.get("email", "").strip().lower()

    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    accept_terms = request.form.get("accept_terms") == "1"

    # ========================================
    # 3. KIỂM TRA DỮ LIỆU
    # ========================================

    if not full_name:
        flash("Vui lòng nhập họ và tên.", "danger")
        return render_template("auth/register.html")

    if len(full_name) > 100:
        flash("Họ và tên không được vượt quá 100 ký tự.", "danger")
        return render_template("auth/register.html")

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.fullmatch(email_pattern, email):
        flash("Địa chỉ email không hợp lệ.", "danger")
        return render_template("auth/register.html")

    if len(email) > 255:
        flash("Email không được vượt quá 255 ký tự.", "danger")
        return render_template("auth/register.html")

    if len(password) < 8:
        flash("Mật khẩu phải có ít nhất 8 ký tự.", "danger")
        return render_template("auth/register.html")

    if password != confirm_password:
        flash("Mật khẩu xác nhận không khớp.", "danger")
        return render_template("auth/register.html")

    if not accept_terms:
        flash("Bạn cần đồng ý với điều khoản sử dụng.", "danger")
        return render_template("auth/register.html")

    # ========================================
    # 4. KIỂM TRA EMAIL VÀ TÌM VAI TRÒ LEARNER
    # ========================================

    try:

        existing_user = db.session.execute(
            text(
                """
                SELECT user_id
                FROM users
                WHERE email = :email
                LIMIT 1
                """
            ),
            {"email": email},
        ).first()

        if existing_user:
            flash("Email này đã được sử dụng.", "danger")
            return render_template("auth/register.html")

        learner_role = db.session.execute(
            text(
                """
                SELECT role_id
                FROM roles
                WHERE role_name = 'LEARNER'
                LIMIT 1
                """
            )
        ).scalar()

        if learner_role is None:
            flash(
                "Hệ thống chưa cấu hình vai trò Học viên.",
                "danger"
            )
            return render_template("auth/register.html")

        # ========================================
        # 5. BĂM MẬT KHẨU
        # ========================================

        password_hash = generate_password_hash(password)

        # ========================================
        # 6. LƯU TÀI KHOẢN VÀO MYSQL
        # ========================================

        db.session.execute(
            text(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    password_hash,
                    role_id,
                    account_status
                )
                VALUES (
                    :full_name,
                    :email,
                    :password_hash,
                    :role_id,
                    'ACTIVE'
                )
                """
            ),
            {
                "full_name": full_name,
                "email": email,
                "password_hash": password_hash,
                "role_id": learner_role,
            },
        )

        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        flash(
            "Email đã được sử dụng hoặc dữ liệu vi phạm ràng buộc.",
            "danger"
        )
        return render_template("auth/register.html")

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception(
            "Database error during learner registration"
        )

        flash(
            "Đã xảy ra lỗi khi tạo tài khoản. Vui lòng thử lại.",
            "danger"
        )
        return render_template("auth/register.html")

    # ========================================
    # 7. THÔNG BÁO VÀ CHUYỂN SANG ĐĂNG NHẬP
    # ========================================

    flash(
        "Đăng ký tài khoản thành công. Vui lòng đăng nhập.",
        "success"
    )

    return redirect(url_for("auth.login"))



@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("auth.login"))
