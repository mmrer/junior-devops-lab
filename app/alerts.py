"""Алерты в Telegram. Шлём только при смене состояния, чтобы не спамить."""

import logging

import httpx

from app.config import SSL_WARN_DAYS, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from app.checker import CheckResult

log = logging.getLogger(__name__)

# Последнее известное состояние каждого сайта: url -> "up" / "down"
_last_state: dict[str, str] = {}
# Сайты, по которым уже предупредили про SSL
_ssl_warned: set[str] = set()


def build_alerts(r: CheckResult) -> list[str]:
    """Решаем, какие сообщения отправить. Чистая логика — тестируется без сети."""
    messages = []
    state = "up" if r.is_up else "down"
    previous = _last_state.get(r.url)

    if previous is not None and previous != state:
        if state == "down":
            messages.append(f"🔴 {r.url} недоступен: {r.error or r.status_code}")
        else:
            messages.append(f"🟢 {r.url} снова работает ({r.status_code}, {r.response_ms} мс)")
    _last_state[r.url] = state

    if r.ssl_days_left is not None and r.ssl_days_left <= SSL_WARN_DAYS:
        if r.url not in _ssl_warned:
            messages.append(f"⚠️ SSL у {r.url} истекает через {r.ssl_days_left} дн.")
            _ssl_warned.add(r.url)
    else:
        _ssl_warned.discard(r.url)

    return messages


def send(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log.info("Telegram не настроен, алерт: %s", message)
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        log.warning("Не удалось отправить алерт: %s", exc)
