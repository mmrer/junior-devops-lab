"""Работа с PostgreSQL: одна таблица с результатами проверок."""

from contextlib import contextmanager

import psycopg

from app.checker import CheckResult
from app.config import DATABASE_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
    id            BIGSERIAL PRIMARY KEY,
    url           TEXT        NOT NULL,
    checked_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_up         BOOLEAN     NOT NULL,
    status_code   INTEGER,
    response_ms   REAL,
    ssl_days_left INTEGER,
    error         TEXT
);
CREATE INDEX IF NOT EXISTS checks_url_time ON checks (url, checked_at DESC);
"""


@contextmanager
def connect():
    with psycopg.connect(DATABASE_URL) as conn:
        yield conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(SCHEMA)


def save_result(r: CheckResult) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO checks (url, is_up, status_code, response_ms, ssl_days_left, error) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (r.url, r.is_up, r.status_code, r.response_ms, r.ssl_days_left, r.error),
        )


def latest_status() -> list[dict]:
    """Последняя проверка по каждому сайту."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ON (url) url, checked_at, is_up, status_code, "
            "response_ms, ssl_days_left, error "
            "FROM checks ORDER BY url, checked_at DESC"
        ).fetchall()
    keys = ["url", "checked_at", "is_up", "status_code", "response_ms", "ssl_days_left", "error"]
    return [dict(zip(keys, row)) for row in rows]


def ping() -> bool:
    """Для healthcheck: жива ли база."""
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False
