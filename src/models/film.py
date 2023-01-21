import orjson
from core.json import orjson_dumps
from pydantic import BaseModel
from uuid import UUID


class Genre(BaseModel):
    id: UUID
    name: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Person(BaseModel):
    id: UUID
    name: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Film(BaseModel):
    id: UUID
    title: str
    imdb_rating: float
    description: str
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class FilmsList(BaseModel):
    count: int
    results: list[Film]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
