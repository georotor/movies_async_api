from functools import lru_cache

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from models.genre import Genre, GenresList
from services.node import NodeService


class GenreService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = Genre
        self.index = 'genres'

    async def get_genres(self, size: int = 10, page_number: int = 1) -> GenresList | None:
        _sort = [
            {"name.raw": {"order": "asc"}},
            {"id": {"order": "asc"}}
        ]

        docs = await self._get_from_elastic(size=size, page_number=page_number, sort=_sort)
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
