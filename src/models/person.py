from uuid import UUID

import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Person(BaseModel):
    id: UUID
    name: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
