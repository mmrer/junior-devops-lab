"""Точка входа: API на FastAPI + фоновая проверка сайтов по расписанию."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from app import alerts, db
from app.checker import check_site
from app.config import CHECK_INTERVAL, SITES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("site-monitor")

# Метрики для Prometheus
SITE_UP = Gauge("site_up", "1 если сайт отвечает, 0 если нет", ["url"])
RESPONSE_MS = Gauge("site_response_ms", "Время ответа в миллисекундах", ["url"])
SSL_DAYS = Gauge("site_ssl_days_left", "Дней до истечения SSL", ["url"])


def run_checks() -> None:
    for url in SITES:
        result = check_site(url)
        db.save_result(result)

        SITE_UP.labels(url).set(1 if result.is_up else 0)
        if result.response_ms is not None:
            RESPONSE_MS.labels(url).set(result.response_ms)
        if result.ssl_days_left is not None:
            SSL_DAYS.labels(url).set(result.ssl_days_left)

        for message in alerts.build_alerts(result):
            alerts.send(message)

        log.info("%s up=%s code=%s %s мс ssl=%s дн.", url, result.is_up,
                 result.status_code, result.response_ms, result.ssl_days_left)


async def scheduler() -> None:
    while True:
        try:
            # Проверки синхронные, поэтому уводим их в поток, чтобы не блокировать API
            await asyncio.to_thread(run_checks)
        except Exception:
            log.exception("Ошибка в цикле проверок")
        await asyncio.sleep(CHECK_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    task = asyncio.create_task(scheduler())
    yield
    task.cancel()


app = FastAPI(title="Site Monitor", lifespan=lifespan)


@app.get("/health")
def health():
    """Для healthcheck в Docker и для проверки после деплоя в CI."""
    return {"status": "ok", "db": db.ping()}


@app.get("/sites")
def sites():
    return {"sites": SITES}


@app.get("/status")
def status():
    return {"results": db.latest_status()}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
