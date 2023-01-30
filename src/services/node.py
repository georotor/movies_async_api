from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Optional
from uuid import UUID

from fastapi_cache.decorator import cache
from orjson import dumps, loads
from pydantic import BaseModel

from db_managers.abstract_manager import AbstractDBManager


class NodeService:
    """Базовый класс для сервисов"""
    Node = BaseModel
    index = None

    def __init__(self, db_manager: AbstractDBManager):
        self.db_manager = db_manager

    @staticmethod
    async def b64decode(s: str) -> ...:
        padding = 4 - (len(s) % 4)
        s = s + ("=" * padding)
        return loads(urlsafe_b64decode(s))

    @staticmethod
    async def b64encode(obj: ...) -> str:
        encoded = urlsafe_b64encode(dumps(obj)).decode()
        return encoded.rstrip("=")

    @cache()
    async def get_by_id(self, node_id: UUID) -> Node | None:
        return await self.db_manager.get(self.index, node_id, self.Node)

    async def _get_from_elastic(
            self, query: dict
    ) -> tuple[Optional[list[Node]], list]:

        res, search_after = await self.db_manager.search_all(
            self.index, self.Node, query
        )

        return res, search_after
