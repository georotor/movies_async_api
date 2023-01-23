from uuid import UUID

import orjson
from pydantic import BaseModel, Field


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Roles(BaseModel):
    actor: list[UUID] = []
    writer: list[UUID] = []
    director: list[UUID] = []

    def __getitem__(self, item):
        return getattr(self, item)

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Person(BaseModel):
    id: UUID
    name: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class PersonDetails(Person):
    roles: Roles = Field(default_factory=Roles)

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class PersonsList(BaseModel):
    count: int
    next: str | None
    results: list[Person]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
