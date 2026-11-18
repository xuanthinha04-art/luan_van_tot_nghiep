from sqlalchemy import text

from .extensions import db


def fetch_one(sql: str, params: dict | None = None):
    row = db.session.execute(text(sql), params or {}).mappings().first()
    return dict(row) if row else None


def fetch_all(sql: str, params: dict | None = None):
    rows = db.session.execute(text(sql), params or {}).mappings().all()
    return [dict(row) for row in rows]


def execute(sql: str, params: dict | None = None):
    result = db.session.execute(text(sql), params or {})
    db.session.commit()
    return result
