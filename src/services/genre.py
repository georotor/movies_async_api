from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre

from services.base import BaseService
from pydantic import BaseModel


class GenreService(BaseService):
    model = Genre
    index = "genres"

    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic=elastic)

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        genre = await self._get_by_id(genre_id)

        return genre

    async def get_genres(self, search_after=None) -> tuple[list[Genre], str]:
        query = {
            "size": 100,
            "sort": [
                {"id": "asc"},
            ],
        }
        result = await self._get_list(query=query, search_after=search_after)
        return result

    async def search(self, query, search_after) -> tuple[list[Genre], str]:
        query = {
            "query": {"match": {"name": {"query": query, "fuzziness": "AUTO"}}},
            "sort": [
                {"id": "asc"},
            ],
        }
        result = await self._search(query=query, search_after=search_after)
        return result


@lru_cache()
def get_genre_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(elastic)
