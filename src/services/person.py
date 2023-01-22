from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person
from models.film import Film


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._get_person_from_elastic(person_id)
        if not person:
            return None

        return person

    async def get_person_films(self, person_id: str, per_page: int, search_after: str) -> tuple[list[Film], str]:
        query = {
            "size": per_page,
            "query": {
                "bool": {
                    "should": [
                        { "nested": { "query": {"term": {"actors.id": person_id}}, "path": "actors", } },
                        { "nested": { "query": {"term": {"writers.id": person_id}}, "path": "writers", } },
                        { "nested": { "query": {"term": {"directors.id": person_id}}, "path": "directors", } },
                    ]
                }
            },
            "sort": [
                {"imdb_rating": "desc"},
                {"id": "desc"}
            ]
        }
        if search_after:
            query["search_after"] = search_after.split(",")

        try:
            doc = await self.elastic.search(index="movies", body=query)
        except NotFoundError:
            return None
        hits = doc["hits"]["hits"]
        search_after = ",".join(map(str, hits[-1].get("sort"))) or []
        return [Film(**film["_source"]) for film in doc["hits"]["hits"]], search_after

    async def get_persons(
        self, per_page=50, search_after: str = None
    ) -> tuple[list[Person], str]:
        query = {"size": per_page, "sort": [{"id": "asc"}]}
        if search_after:
            query["search_after"] = search_after.split(",")

        try:
            doc = await self.elastic.search(index="persons", body=query)
        except NotFoundError:
            return None
        hits = doc["hits"]["hits"]
        search_after = ",".join(map(str, hits[-1].get("sort"))) or []
        return [
            Person(**person["_source"]) for person in doc["hits"]["hits"]
        ], search_after

    async def search(
        self, query, per_page: int = 50, search_after: str = None
    ) -> tuple[list[Person], str]:
        query = {
            "size": per_page,
            "query": {"match": {"name": {"query": query, "fuzziness": "AUTO"}}},
            "sort": [{"id": "asc"}],
        }
        if search_after:
            query["search_after"] = search_after.split(",")
        try:
            doc = await self.elastic.search(index="persons", body=query)
        except NotFoundError:
            return None
        hits = doc["hits"]["hits"]
        search_after = ",".join(map(str, hits[-1].get("sort"))) or []
        return [Person(**person["_source"]) for person in hits], search_after

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
