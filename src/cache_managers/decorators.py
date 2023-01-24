"""Декоратор для кэша ES. Вешается на методы классов из services. В качестве
аргумента принимает модель pydantic для валидации данных. Вероятно,
инициализацию redis лучше вынести из этого файла в main. Иначе создается
дополнительное подключение.

Пример для film.py:

from src.cache_managers.decorators import redis_cache.

class FilmService(BaseService):
    model = Film
    ...

    @redis_cache.pydantic_cache(model)
    async def get_films(...):

"""


from functools import wraps

import aioredis
import orjson
from pydantic import BaseModel
from src.cache_managers.abstract_manager import AbstractManager
from src.cache_managers.redis_manager import RedisManager
from src.core.config import REDIS_HOST, REDIS_PORT


class Cache:
    def __init__(self, cache_manager: AbstractManager):
        self.cache_manager = cache_manager

    @staticmethod
    def _parse_list(model: BaseModel, raw_data: list) -> tuple:
        """Валидация данных для сложного запроса с дополнительными аргументами.

        Args:
            model - модель pydantic для валидации и декодирования данных;
            raw_data - список, где первым аргументом идет список с "сырыми"
            данными моделей, затем дополнительные данные (пр. search_after);
        Returns:
            Кортеж, в котором первый элемент меняется на список моделей,
            а остальные остается без изменения

        """
        models_list = [model.parse_raw(x) for x in raw_data[0]]
        additional_vars = raw_data[1:]
        return models_list, *additional_vars

    @staticmethod
    def is_serializable(value) -> bool:
        """Проверяет, можно ли закодировать аргумент value в json. Позволяет
        игнорировать аргументы вроде self (при декорации методов).

        Args:
            value - данные любого типа;

        """
        try:
            orjson.dumps(value)
            return True
        except TypeError:
            return False

    def pydantic_cache(self, model: BaseModel):
        """Декоратор, добавляет поддержку кэширования.

        Args:
            model - модель pydantic для валидации и декодирования данных;
        Returns:
            В зависимости от типа декорируемой функции - либо одну модель,
            либо кортеж из списка моделей и дополнительных аргументов
             -> BaseModel | tuple[list[BaseModel], Any]

        """

        def wrapper(func):
            @wraps(func)
            async def inner(*args, **kwargs):
                _args = [i for i in args if self.is_serializable(i)]
                cache_id = self.cache_manager.create_id((_args, kwargs))
                cache_value = await self.cache_manager.get(cache_id)

                if cache_value:
                    decode_value = orjson.loads(cache_value)
                    if isinstance(decode_value, list):
                        return self._parse_list(model, decode_value)
                    return model.parse_raw(decode_value)

                else:
                    fresh_value = await func(*args, **kwargs)
                    await self.cache_manager.put(
                        cache_id,
                        orjson.dumps(fresh_value, default=model.json),
                    )
                    return fresh_value

            return inner
        return wrapper


redis = aioredis.from_url(
    "{}:{}".format(REDIS_HOST, REDIS_PORT), decode_responses=True,
)

redis_cache = Cache(RedisManager(redis, ttl=10))
