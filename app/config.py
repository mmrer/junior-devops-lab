"""Настройки приложения. Всё берётся из переменных окружения (файл .env)."""

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://monitor:monitor@db:5432/monitor")

# Список сайтов через запятую: https://example.com,https://python.org
SITES = [s.strip() for s in os.getenv("SITES", "https://example.com").split(",") if s.strip()]

# Как часто проверять сайты, в секундах
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

# Таймаут одной проверки, в секундах
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "10"))

# За сколько дней до истечения SSL слать предупреждение
SSL_WARN_DAYS = int(os.getenv("SSL_WARN_DAYS", "7"))

# Telegram-алерты. Если не заданы — алерты просто не отправляются
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
