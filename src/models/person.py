import orjson
from core.json import orjson_dumps
from pydantic import BaseModel, Field
from uuid import UUID


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
    roles: Roles = Field(default_factory=Roles)

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class PersonsList(BaseModel):
    count: int
    results: list[Person]
