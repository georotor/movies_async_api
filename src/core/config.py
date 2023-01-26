from logging import config as logging_config

from pydantic import BaseSettings

from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    project_name: str = 'movies'
    elastic_host: str = 'localhost'
    elastic_port: int = 9200
    redis_host: str = 'localhost'
    redis_port: int = 6379
    cache_expire: int = 300


settings = Settings()

