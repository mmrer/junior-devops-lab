junior-devops-lab

домашняя лаба по git/docker/ci|cd/ansible

# Site Monitor

Сервис мониторинга сайтов: проверяет доступность, время ответа и срок SSL-сертификата, хранит историю в PostgreSQL, отдаёт метрики для Prometheus и шлёт алерты в Telegram.

Пет-проект для практики DevOps: Docker, CI/CD, Ansible, мониторинг.

## Стек

- Python 3.12, FastAPI
- PostgreSQL 16
- Docker, docker-compose
- Prometheus-метрики, алерты в Telegram

## Запуск

```bash
cp .env.example .env      # заполни пароль и список сайтов
docker compose up -d --build
curl localhost:8000/health
```

## API

| Эндпоинт   | Что отдаёт                              |
|------------|-----------------------------------------|
| `/health`  | Жив ли сервис и база                    |
| `/sites`   | Список отслеживаемых сайтов             |
| `/status`  | Последняя проверка по каждому сайту     |
| `/metrics` | Метрики в формате Prometheus            |

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

## Дорожная карта

- [x] Приложение, база, Docker
- [ ] CI на GitHub Actions: линтер → тесты → сборка образа
- [ ] Деплой на VPS из CI
- [ ] Nginx как reverse proxy с SSL
- [ ] Ansible-плейбук для настройки сервера с нуля
- [ ] Prometheus + Grafana
- [ ] Бэкапы базы по расписанию

