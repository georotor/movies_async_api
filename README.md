# Movies: Async API для кинотеатра

[![CI](https://github.com/georotor/movies_async_api/actions/workflows/tests.yml/badge.svg)](https://github.com/georotor/movies_async_api/actions/workflows/tests.yml)

## Архитектура

![Архитектура](https://github.com/georotor/movies_async_api/blob/main/doc/schema.png?raw=true)

## Компоненты сервиса
- [FastAPI - реализация API](https://github.com/georotor/movies_async_api/tree/main/src)
- Elasticsearch - хранилище
- Redis - хранилище для кэша

## Запуск сервиса

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

После старта будет доступен [Swagger API](http://127.0.0.1/api/openapi).

## Тесты
Запуск тестов осуществляется командой:
```bash
docker-compose -f src/tests/functional/docker-compose.yml up --build
```
