"""Тесты без сети и без базы — их будет гонять CI."""

from datetime import UTC, datetime

from app import alerts
from app.checker import CheckResult, days_until, parse_cert_date


def test_parse_cert_date():
    dt = parse_cert_date("Jun  1 12:00:00 2027 GMT")
    assert dt == datetime(2027, 6, 1, 12, 0, tzinfo=UTC)


def test_days_until():
    now = datetime(2027, 1, 1, tzinfo=UTC)
    assert days_until(datetime(2027, 1, 11, tzinfo=UTC), now) == 10


def _result(url="https://x.test", up=True, ssl=90):
    return CheckResult(url, up, 200 if up else None, 50.0, ssl, None if up else "timeout")


def test_alert_on_down_and_recovery():
    alerts._last_state.clear()
    assert alerts.build_alerts(_result(up=True)) == []          # первый раз — просто запомнили
    assert "недоступен" in alerts.build_alerts(_result(up=False))[0]
    assert alerts.build_alerts(_result(up=False)) == []         # повторно не спамим
    assert "снова работает" in alerts.build_alerts(_result(up=True))[0]


def test_ssl_warning_sent_once():
    alerts._last_state.clear()
    alerts._ssl_warned.clear()
    assert "SSL" in alerts.build_alerts(_result(url="https://s.test", ssl=3))[0]
    assert alerts.build_alerts(_result(url="https://s.test", ssl=2)) == []
