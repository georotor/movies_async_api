import inspect
from functools import wraps
from typing import Any, Callable, Optional, Type

from fastapi_cache import FastAPICache
from fastapi_cache.coder import Coder
from pydantic import BaseModel


def pydantic_cache(
        model: Type[BaseModel],
        expire: Optional[int] = None,
        coder: Optional[Type[Coder]] = None,
        key_builder: Optional[Callable[..., Any]] = None,
        namespace: Optional[str] = "",
):
    """
    Декоратор для кэширования через fastapi-cache.
    Возвращает результат в виде Pydantic объекта или None.

    :param model: Pydantic класс для возвращаемого объекта.
    :param expire: Время жизни кэша.
    :param coder: Класс для кодирования кэша.
    :param key_builder: Функция построения ключа для кэша.
    :param namespace: Пространство имен для ключа кэша.
    :return: None или объект класса model.
    """
    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            nonlocal model
            nonlocal coder
            nonlocal expire
            nonlocal key_builder

            coder = coder or FastAPICache.get_coder()
            expire = expire or FastAPICache.get_expire()
            key_builder = key_builder or FastAPICache.get_key_builder()
            backend = FastAPICache.get_backend()

            if inspect.iscoroutinefunction(key_builder):
                cache_key = await key_builder(
                    func,
                    namespace,
                    args=args,
                    kwargs=kwargs,
                )
            else:
                cache_key = key_builder(
                    func,
                    namespace,
                    args=args,
                    kwargs=kwargs,
                )

            try:
                cache_value = await backend.get(cache_key)
            except ConnectionError:
                cache_value = None

            if cache_value is not None:
                decode_value = coder.decode(cache_value)
                if decode_value is not None:
                    return model.parse_obj(decode_value)
                return decode_value

            fresh_value = await func(*args, **kwargs)
            try:
                await backend.set(
                    cache_key, coder.encode(fresh_value), expire or FastAPICache.get_expire()
                )
            except ConnectionError:
                pass

            return fresh_value

        return inner

    return wrapper
