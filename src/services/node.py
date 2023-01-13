from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from pydantic import BaseModel
from fastapi_cache.decorator import cache

NODE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class NodeService:
    """Базовый класс для сервисов"""
    Node = BaseModel
    index = None

    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_by_id(self, node_id: UUID) -> Node | None:
        doc = await self._get_node_from_elastic(node_id)
        if not doc:
            return None

        return self.Node(**doc['_source'])

    async def get(self, query: dict | None = None, sort: list | None = None,
                  page_number=1, size=10) -> list[Node] | None:
        docs = await self._get_from_elastic(query=query, sort=sort, size=size, page_number=page_number)
        if not docs:
            return None

        return [self.Node(**doc['_source']) for doc in docs['hits']['hits']]

    @cache(expire=NODE_CACHE_EXPIRE_IN_SECONDS)
    async def _get_from_elastic(self, index: str | None = None, query: dict | None = None, sort: list | None = None,
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
