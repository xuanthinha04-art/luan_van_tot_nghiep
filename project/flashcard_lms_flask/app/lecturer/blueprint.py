# Blueprint được khởi tạo tại app/lecturer/__init__.py quản lý các route của khu vực Giảng viên.

from flask import Blueprint


lecturer_bp = Blueprint(
    "lecturer",
    __name__,
    url_prefix="/lecturer",
)