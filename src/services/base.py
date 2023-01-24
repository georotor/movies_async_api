from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis


from enum import Enum
from pydantic import BaseModel


class BaseService:
    model = BaseModel
    index = None

    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def _get_by_id(self, id_: str) -> Optional[model]:
        try:
            doc = await self.elastic.get(self.index, id_)
        except NotFoundError:
            return None
        return_model = self.model(**doc["_source"])

        if not return_model:
            return None

        return return_model

    async def _get_list(
        self,
        query,
        search_after=None,
    ) -> tuple[list[model], str]:

        if search_after:
            query["search_after"] = search_after.split(",")

        try:
            doc = await self.elastic.search(index=self.index, body=query)
        except NotFoundError:
            return None
        hits = doc["hits"]["hits"]
        search_after = ",".join(map(str, hits[-1]["sort"]))
        return [(self.model(**hit["_source"])) for hit in hits], search_after

    async def _search(self, query, search_after) -> tuple[list[model], str]:
        if search_after:
            query["search_after"] = search_after.split(",")

        try:
            doc = await self.elastic.search(index=self.index, body=query)
        except NotFoundError:
            return None
        hits = doc["hits"]["hits"]
        search_after = ",".join(map(str, hits[-1]["sort"]))
        return [(self.model(**hit["_source"])) for hit in hits], search_after
