from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from models.genre import Genre, GenresList
from services.node import NodeService


class GenreService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = Genre
        self.index = 'genres'

    async def get(self, size: int = 10, page_number: int = 1) -> GenresList | None:
        sorting = [{"name.raw": "asc"}]

        docs = await self._get_from_elastic(sort=sorting, size=size, page_number=page_number)
        if not docs:
            return None

        return GenresList(
            count=docs['hits']['total']['value'],
            results=[Genre(**doc['_source']) for doc in docs['hits']['hits']]
        )


@lru_cache()
def get_genre_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(elastic)
