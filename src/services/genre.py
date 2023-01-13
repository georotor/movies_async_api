from models.genre import Genre
from services.node import NodeService

from functools import lru_cache
from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis


class GenreService(NodeService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        super().__init__(redis, elastic)
        self.Node = Genre
        self.index = 'genres'

    async def get_all(self):
        genres = await self._get_all_from_elastic()
        return genres

    async def _get_all_from_elastic(self) -> list[Genre]:
        try:
            docs = await self.elastic.search(index=self.index, body={"query": {"match_all": {}}})
        except NotFoundError:
            return None

        return [Genre(**doc['_source']) for doc in docs['hits']['hits']]


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)