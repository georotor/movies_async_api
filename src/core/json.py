import orjson
from fastapi_cache.coder import Coder
from pydantic import BaseModel
from starlette.responses import JSONResponse


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()


def default(obj):
    if isinstance(obj, BaseModel):
        return obj.json()


class JsonCoder(Coder):
    @classmethod
    def encode(cls, value: ...) -> str:
        if isinstance(value, JSONResponse):
            return value.body

        if isinstance(value, BaseModel):
            return value.json()

        return orjson.dumps(value, default=default).decode()

    @classmethod
    def decode(cls, value: ...) -> ...:
        return orjson.loads(value)
