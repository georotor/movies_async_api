from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._get_person_from_elastic(person_id)
        if not person:
            return None

        return person

    async def get_persons(
        self,
        page=1,
        per_page=50,
    ) -> list[Person]:
        from_ = (page - 1) * per_page
        query = {
            "from": from_,
            "size": per_page,
        }
        try:
            doc = await self.elastic.search(index="persons", body=query)
        except NotFoundError:
            return None
        return [Person(**person["_source"]) for person in doc["hits"]["hits"]]

    async def search(self, query) -> list[Person]:
        query = {
            "query": {"match": {"name": {"query": query, "fuzziness": "AUTO"}}},
        }
        try:
            doc = await self.elastic.search(index="persons", body=query)
        except NotFoundError:
            return None
        return [Person(**person["_source"]) for person in doc["hits"]["hits"]]

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        try:
            doc = await self.elastic.get("persons", person_id)
        except NotFoundError:
            return None
        return Person(**doc["_source"])


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
