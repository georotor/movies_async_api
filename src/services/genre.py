from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        genre = await self._get_genre_from_elastic(genre_id)
        if not genre:
            return None

        return genre

    async def get_genres(
        self,
    ) -> list[Genre]:
        query = {
            "size": 100,
        }
        try:
            doc = await self.elastic.search(index="genres", body=query)
        except NotFoundError:
            return None
        return [Genre(**genre["_source"]) for genre in doc["hits"]["hits"]]

    async def search(self, query) -> list[Genre]:
        query = {
            "query": {"match": {"name": {"query": query, "fuzziness": "AUTO"}}},
        }
        try:
            doc = await self.elastic.search(index="genres", body=query)
        except NotFoundError:
            return None
        return [Genre(**genre["_source"]) for genre in doc["hits"]["hits"]]

    async def _get_genre_from_elastic(self, genre_id: str) -> Optional[Genre]:
        try:
            doc = await self.elastic.get("genres", genre_id)
        except NotFoundError:
            return None
        return Genre(**doc["_source"])


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
