import hashlib
from abc import ABC, abstractmethod

import orjson


class AbstractManager(ABC):
    @staticmethod
    def create_id(value):
        """Результаты запросов нужно искать / хранить в кэше. Для этого нужен
        какой-то ключ. Для простых запросов, возвращающих один единственный
        объект, ключом может быть id объекта. Для сложных запросов,
        возвращающих список значений, так не получится. Один из вариантов -
        хэшировать входящие данные запроса.

        """
        str_value = orjson.dumps(value)
        _hash = hashlib.md5(str_value).hexdigest()
        return str(_hash)

    @abstractmethod
    async def put(self, key, value):
        """Записать значение в кэш"""

    @abstractmethod
    async def get(self, key):
        """Получить значение из кэша"""
