from uuid import UUID

import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Genre(BaseModel):
    id: UUID
    name: str
    films_count: int
    description: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class GenresList(BaseModel):
    count: int
    results: list[Genre]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
