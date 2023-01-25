# Проектное задание: Async API

Репозиторий с Async API: https://github.com/georotor/Async_API_sprint_1

В проекте используется ETL: https://github.com/georotor/new_admin_panel_sprint_3


Для запуска потребуется два файла с переменными окружения:

- `.env` с настройками ETL:
```bash
cp .env.example .env
```

- `.env.db` с настройками Postgresql:
```bash
cp .env.db.example .env.db
```

Запуск API осуществляется командой:
```bash
docker-compose up -d --build
```
Т.к. контейнер с ETL запускается из github.com по ssh ссылке, перед запуском может потребоваться установить две переменные окружения:
```bash
export DOCKER_BUILDKIT=0 && export COMPOSE_DOCKER_CLI_BUILD=0
```
