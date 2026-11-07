"""Проверка сайта: доступность, код ответа, время ответа, срок SSL."""

import socket
import ssl
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx

from app.config import REQUEST_TIMEOUT


@dataclass
class CheckResult:
    url: str
    is_up: bool
    status_code: int | None
    response_ms: float | None
    ssl_days_left: int | None
    error: str | None


def days_until(expires_at: datetime, now: datetime | None = None) -> int:
    """Сколько полных дней осталось до даты. Отдельная функция — её легко тестировать."""
    now = now or datetime.now(UTC)
    return (expires_at - now).days


def parse_cert_date(value: str) -> datetime:
    """Дата из сертификата выглядит так: 'Jun  1 12:00:00 2027 GMT'."""
    return datetime.strptime(value, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)


def get_ssl_days_left(url: str) -> int | None:
    """Подключаемся к хосту по TLS и читаем дату истечения сертификата."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    port = parsed.port or 443
    context = ssl.create_default_context()
    with (
        socket.create_connection((parsed.hostname, port), timeout=REQUEST_TIMEOUT) as sock,
        context.wrap_socket(sock, server_hostname=parsed.hostname) as tls,
    ):
        cert = tls.getpeercert()
    return days_until(parse_cert_date(cert["notAfter"]))


def check_site(url: str) -> CheckResult:
    """Одна проверка сайта. Никогда не падает: любая ошибка попадает в поле error."""
    start = time.monotonic()
    try:
        response = httpx.get(url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        is_up = response.status_code < 500
        status_code, error = response.status_code, None
    except httpx.HTTPError as exc:
        return CheckResult(url, False, None, None, None, f"{type(exc).__name__}: {exc}")

    try:
        ssl_days = get_ssl_days_left(url)
    except (ssl.SSLError, OSError, KeyError, ValueError) as exc:
        ssl_days, error = None, f"SSL: {exc}"

    return CheckResult(url, is_up, status_code, elapsed_ms, ssl_days, error)
