from pydantic import BaseModel, BaseSettings


class Logging(BaseModel):
    level_root: str = 'INFO'
    level_uvicorn: str = 'INFO'
    level_console: str = 'DEBUG'


class Settings(BaseSettings):
    project_name: str = 'movies'
    elastic_host: str = 'localhost'
    elastic_port: int = 9200
    redis_host: str = 'localhost'
    redis_port: int = 6379
    cache_expire: int = 300
    logging: Logging = Logging()

    class Config:
        env_nested_delimiter = '__'


settings = Settings()

