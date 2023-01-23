import logging
from base64 import urlsafe_b64encode, urlsafe_b64decode
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from orjson import dumps, loads
from pydantic import BaseModel
from fastapi_cache.decorator import cache

NODE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class NodeService:
    """Базовый класс для сервисов"""
    Node = BaseModel
    index = None

    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    @staticmethod
    async def b64decode(s: str) -> ...:
        padding = 4 - (len(s) % 4)
        s = s + ("=" * padding)
        return loads(urlsafe_b64decode(s))

    @staticmethod
    async def b64encode(obj: ...) -> str:
        encoded = urlsafe_b64encode(dumps(obj)).decode()
        return encoded.rstrip("=")

    async def get_by_id(self, node_id: UUID) -> Node | None:
        doc = await self._get_node_from_elastic(node_id)
        if not doc:
            return None

        return self.Node(**doc['_source'])

    @cache(expire=NODE_CACHE_EXPIRE_IN_SECONDS)
    async def _get_from_elastic(self, index: str | None = None, query: dict | None = None,
                                search_after: list | None = None, sort: list | None = None,
                                page_number=1, size=10) -> dict | None:

        if not index:
            index = self.index

        body = {
            "from": (page_number - 1) * size,
            "size": size,
            "query": {"match_all": {}}
        }

        if query:
            body["query"] = query

        if sort:
            body["sort"] = sort

            if search_after:
                # search_after не работает без сортировки
                del body["from"]
                body["search_after"] = search_after

                if len(sort) != len(search_after):
                    logging.error("search_after has {0} value(s) but sort has {1}".format(
                        len(search_after),
                        len(sort)
                    ))
                    return None

        try:
            docs = await self.elastic.search(index=index, body=body)
        except NotFoundError:
            return None

        return docs

    @cache(expire=NODE_CACHE_EXPIRE_IN_SECONDS)
    async def _get_node_from_elastic(self, node_id: UUID) -> Node | None:
        try:
            doc = await self.elastic.get(self.index, node_id)
        except NotFoundError:
            return None
        return doc
