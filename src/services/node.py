from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Optional
from uuid import UUID

from orjson import dumps, loads
from pydantic import BaseModel

from cache.pydantic_cache import pydantic_cache
from db_managers.abstract_manager import AbstractDBManager


class NodeService:
    """Базовый класс для сервисов."""
    Node = BaseModel
    index = None

    def __init__(self, db_manager: AbstractDBManager):
        self.db_manager = db_manager

    @staticmethod
    async def b64decode(s: str) -> ...:
        """Декодирование данных search_after полученных из URL."""
        padding = 4 - (len(s) % 4)
        s = s + ("=" * padding)
        return loads(urlsafe_b64decode(s))

    @staticmethod
    async def b64encode(obj: ...) -> str:
        """Кодирование данных search_after для хранения в URL."""
        encoded = urlsafe_b64encode(dumps(obj)).decode()
        return encoded.rstrip("=")

    # @cache()
    async def get_by_id(self, node_id: UUID) -> Optional[Node]:
        """Get запрос, должен возвращать один единственный объект. Осуществляем
        вызов через вложенную функцию, чтобы можно было передать внутрь
        декоратора модель self.Node.

        Args:
          node_id: уникальный идентификатор объекта;

        Returns:
            Экземпляр pydantic BaseModel с данными из БД.

        """
        @pydantic_cache(model=self.Node)
        async def inner(*args, **kwargs):
            return await self.db_manager.get(*args, **kwargs)

        return await inner(self.index, node_id, self.Node)

    async def _get_from_elastic(
            self, query: dict
    ) -> tuple[list[Optional[Node]], int, list]:
        """Комплексный запрос в БД. Возвращает список объектов и значение
        search_after.

        Args:
          query: сформированное тело запроса;

        Returns:
            Кортеж из трех значений:
              - список моделей pydantic BaseModel с данными из БД;
              - общее количество найденных записей (без учета пагинации);
              - значение search_after (стартовое значение для следующей выдачи,
                термин из Elastic, при желании можно реализовать и для SQL).

        """
        res, total, search_after = await self.db_manager.search_all(
            self.index, self.Node, query
        )

        return res, total, search_after
