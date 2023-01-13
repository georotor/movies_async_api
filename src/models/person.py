import orjson
from core.json import orjson_dumps
from pydantic import BaseModel
from uuid import UUID


class Roles(BaseModel):
    actors: list[UUID] | None
    writers: list[UUID] | None
    directors: list[UUID] | None


class Person(BaseModel):
    id: UUID
    name: str
    roles: dict[str, list[UUID]] | None

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
