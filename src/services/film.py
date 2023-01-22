from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film


from enum import Enum


class SortField(str, Enum):
    IMDB_RATING = "imdb_rating"


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await self._get_film_from_elastic(film_id)
        if not film:
            return None

        return film

    async def get_films(
        self,
        sort_field=SortField.IMDB_RATING,
        sort_order="desc",
        genre=None,
        per_page=50,
        search_after=None,
    ) -> tuple[list[Film], str]:
        query = {
            "size": per_page,
            "sort": [{sort_field: sort_order}, {"id": sort_order}],
        }
        if genre:
            query["query"] = (
                {"nested": {"query": {"term": {"genre.id": genre}}, "path": "genre"}},
            )

        if search_after:
            query["search_after"] = search_after.split(",")

        try:
            doc = await self.elastic.search(index="movies", body=query)
        except NotFoundError:
            return None
        hits = doc["hits"]["hits"]
        search_after = ",".join(map(str, hits[-1]["sort"]))
        return [(Film(**film["_source"])) for film in hits], search_after

    async def search(self, query, per_page, search_after) -> tuple[list[Film], list]:
        query = {
            "size": per_page,
            "query": {
                "multi_match": {"query": query, "fields": ["title^3", "description"]}
            },
            "sort": {"imdb_rating": "desc", "id": "desc"},
        }
        if search_after:
            query["search_after"] = search_after.split(",")

        try:
            doc = await self.elastic.search(index="movies", body=query)
        except NotFoundError:
            return None
        hits = doc["hits"]["hits"]
        search_after = ",".join(map(str, hits[-1]["sort"]))
        return [(Film(**film["_source"])) for film in hits], search_after

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.elastic.get("movies", film_id)
        except NotFoundError:
            return None
        return Film(**doc["_source"])


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
