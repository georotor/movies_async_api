from typing import Callable, Optional

from starlette.requests import Request
from starlette.responses import Response


async def key_builder(
        func: Callable,
        namespace: Optional[str] = "",
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
) -> str:
    """
    Сборщик ключа для кэша. Отличается от стандартного билдера fastapi-cache отсутствием хеширования ключа.

    """
    from fastapi_cache import FastAPICache

    prefix = f"{FastAPICache.get_prefix()}:{namespace}:"
    cache_key = (
            prefix
            + f"{func.__module__}:{func.__name__}:{args}:{kwargs}"
    )
    return cache_key
