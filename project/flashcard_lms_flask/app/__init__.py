# //Khởi tạo Flask và đăng ký các thành phần.
import click
from flask import Flask, flash, redirect, render_template, url_for
from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from config import Config
from .extensions import csrf, db, login_manager
from .auth.models import AuthUser
from .auth.routes import auth_bp, load_auth_user
from .lecturer.routes import lecturer_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def user_loader(user_id):
        try:
            return load_auth_user(user_id)
        except SQLAlchemyError:
            db.session.rollback()
            return None

    app.register_blueprint(auth_bp)
    app.register_blueprint(lecturer_bp)

    @app.get("/")
    def index():
        if current_user.is_authenticated and getattr(current_user, "role_name", None) == "LECTURER":
            return redirect(url_for("lecturer.dashboard"))
        return redirect(url_for("auth.login"))

    @app.get("/health/db")
    def database_health():
        try:
            result = db.session.execute(text("SELECT DATABASE() AS database_name, VERSION() AS mysql_version")).mappings().first()
            return {
                "ok": True,
                "database": result["database_name"],
                "mysql_version": result["mysql_version"],
            }
        except SQLAlchemyError as exc:
            db.session.rollback()
            return {"ok": False, "error": str(exc.__class__.__name__)}, 503

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.cli.command("create-lecturer")
    @click.option("--name", prompt="Họ và tên")
    @click.option("--email", prompt="Email")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_lecturer(name, email, password):
        """Tạo tài khoản Lecturer thử nghiệm qua CLI; không mở endpoint tạo tài khoản công khai."""
        email = email.strip().lower()
        existing = db.session.execute(
            text("SELECT user_id FROM users WHERE email=:email"),
            {"email": email},
        ).first()
        if existing:
            raise click.ClickException("Email này đã tồn tại.")

        role_id = db.session.execute(
            text("SELECT role_id FROM roles WHERE role_name='LECTURER'"),
        ).scalar()
        if not role_id:
            raise click.ClickException("Không tìm thấy vai trò LECTURER trong bảng roles.")

        db.session.execute(
            text(
                """
                INSERT INTO users
                    (full_name, email, password_hash, role_id, account_status)
                VALUES
                    (:name, :email, :password_hash, :role_id, 'ACTIVE')
                """
            ),
            {
                "name": name.strip(),
                "email": email,
                "password_hash": generate_password_hash(password),
                "role_id": role_id,
            },
        )
        db.session.commit()
        click.echo(f"Đã tạo tài khoản Lecturer: {email}")

    return app
