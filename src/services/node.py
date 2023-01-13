from uuid import UUID

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from pydantic import BaseModel

NODE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class NodeService:
    Node = BaseModel
    index = None

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, node_id: UUID) -> Node | None:
        node = await self._node_from_cache(str(node_id))
        if not node:
            node = await self._get_node_from_elastic(node_id)
            if not node:
                return None

            await self._put_node_to_cache(str(node_id), node)
        return node

    async def get(self, query: dict | None = None, sort: list | None = None,
                  page_number=1, size=10) -> list[Node] | None:
        docs = await self._get_from_elastic(query=query, sort=sort, size=size, page_number=page_number)
        if not docs:
            return None

        return [self.Node(**doc['_source']) for doc in docs['hits']['hits']]

    async def _get_from_elastic(self, index: str | None = None, query: dict | None = None, sort: list | None = None,
                                page_number=1, size=10) -> dict | None:
        body = {
            "from": (page_number - 1) * size,
            "size": size,
            "query": {"match_all": {}}
        }

        if not index:
            index = self.index

        if query:
            body["query"] = query

        if sort:
            body["sort"] = sort

        try:
            docs = await self.elastic.search(index=index, body=body)
        except NotFoundError:
            return None

        return docs

    async def _get_node_from_elastic(self, node_id: UUID) -> Node | None:
        try:
            doc = await self.elastic.get(self.index, node_id)
        except NotFoundError:
            return None
        return self.Node(**doc['_source'])

    async def _node_from_cache(self, node_id: UUID) -> Node | None:
        data = await self.redis.get(node_id)
        if not data:
            return None

        node = self.Node.parse_raw(data)
        return node

    async def _put_node_to_cache(self, key: str, node: Node):
        await self.redis.set(key, node.json(), expire=NODE_CACHE_EXPIRE_IN_SECONDS)
