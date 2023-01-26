import orjson
from pydantic import BaseModel

from core.json import orjson_dumps


class Node(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
