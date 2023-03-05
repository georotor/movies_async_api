from logging import config as logging_config

import redis.asyncio as aioredis
import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from api.v1 import films, genres, persons
from cache.coder import JsonCoder
from cache.key_builder import key_builder
from core.auth import AuthError, check_auth_url
from core.backoff import BackoffError
from core.config import settings
from core.logger import LOGGING
from db import elastic, redis
from db_managers.abstract_manager import DBManagerError

logging_config.dictConfig(LOGGING)

app = FastAPI(
    title=settings.project_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.exception_handler(DBManagerError)
async def db_exception_handler(request: Request, exc: DBManagerError):
    """Перехватываем ошибки в работе БД. Пока мы работаем с БД через одну из
    реализаций AbstractDBManager это будет DBManagerError.

    """
    return ORJSONResponse(
        status_code=422,
        content={
            "message": "DataBase error: {}".format(exc)},
    )


@app.on_event("startup")
async def startup():
    redis.redis = await aioredis.from_url(
        f"redis://{settings.redis_host}:{settings.redis_port}",
        encoding="utf8",
        decode_responses=True,
        max_connections=20,
    )
    FastAPICache.init(
        RedisBackend(redis.redis),
        prefix="cache",
        coder=JsonCoder,
        expire=settings.cache_expire,
        key_builder=key_builder
    )
    elastic.es = AsyncElasticsearch(
        hosts=[f"{settings.elastic_host}:{settings.elastic_port}"]
    )


@app.on_event("shutdown")
async def shutdown():
    await redis.redis.close()
    await elastic.es.close()


@app.middleware('http')
async def authenticate_user(request: Request, call_next):
    """Используем декоратор middleware('http'):
    https://fastapi.tiangolo.com/tutorial/middleware/

    Обращаемся к ручке auth сервиса для проверки токена. Если токен валидный -
    ручка возвращает status.HTTP_200_OK и список ролей.

    Мы разделяем аутентифицированного пользователя без списка ролей (ему
    назначаем роль 'Guest') и пользователя, вообще не прошедшего аутентификацию
    (ему выдаем роль 'Anonymous').

    """
    try:
        roles = await check_auth_url(request)
    except BackoffError:
        roles = ['Anonymous']
    request.state.auth = roles
    response = await call_next(request)
    return response


app.include_router(films.router, prefix="/api/v1/films", tags=["films"])
app.include_router(persons.router, prefix="/api/v1/persons", tags=["persons"])
app.include_router(genres.router, prefix="/api/v1/genres", tags=["genres"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
