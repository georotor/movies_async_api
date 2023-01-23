from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import BaseModel

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person
from models.film import Film
from services.base import BaseService


class PersonService(BaseService):
    model = Person
    index = "persons"

    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic=elastic)

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._get_by_id(person_id)

        return person

    async def get_persons(
        self, per_page=50, search_after: str = None
    ) -> tuple[list[Person], str]:
        query = {"size": per_page, "sort": [{"id": "asc"}]}
        persons = await self._get_list(search_after=search_after, query=query)
        return persons

    async def search(
        self, query, per_page: int = 50, search_after: str = None
    ) -> tuple[list[Person], str]:
        query = {
            "size": per_page,
            "query": {"match": {"name": {"query": query, "fuzziness": "AUTO"}}},
            "sort": [{"id": "asc"}],
        }
        result = await self._search(query=query, search_after=search_after)
        return result

    async def get_person_films(
        self, person_id: str, per_page: int, search_after: str
    ) -> tuple[list[Film], str]:
        # fmt: off
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
            "sort": [{"imdb_rating": "desc"}, {"id": "desc"}],
        }
        # fmt: on
        if search_after:
            query["search_after"] = search_after.split(",")

        try:
            doc = await self.elastic.search(index="movies", body=query)
        except NotFoundError:
            return None
        hits = doc["hits"]["hits"]
        search_after = ",".join(map(str, hits[-1].get("sort"))) or []
        return [Film(**film["_source"]) for film in doc["hits"]["hits"]], search_after


@lru_cache()
def get_person_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(elastic)
