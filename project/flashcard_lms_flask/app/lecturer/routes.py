"""
Điểm nạp và đăng ký các route của khu vực Lecturer.
"""

from .blueprint import lecturer_bp

# Nạp các module để đăng ký route lên lecturer_bp.
from . import dashboard  # noqa: F401
from . import courses  # noqa: F401
from . import lessons  # noqa: F401
from . import flashcards  # noqa: F401
from . import enrollments  # noqa: F401