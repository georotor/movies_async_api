import orjson
from core.json import orjson_dumps
from pydantic import BaseModel


class Genre(BaseModel):
    id: str
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
