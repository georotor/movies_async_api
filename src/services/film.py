from functools import lru_cache
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from models.film import Film, FilmsList
from services.node import NodeService


class FilmService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = Film
        self.index = 'movies'

    async def search(self, query: str, page_number=1, size=10) -> FilmsList | None:
        _query = {
            "bool": {
                "should": [
                    {"query_string": {"query": query}},
                    {"match": {"title": query}}
                ]
            }
        }

        docs = await self._get_from_elastic(query=_query, size=size, page_number=page_number)
        if not docs:
            return None

        return FilmsList(
            count=docs['hits']['total']['value'],
            results=[Film(**doc['_source']) for doc in docs['hits']['hits']]
        )

    async def get(self, sort: str | None, filter_genre: UUID | None, size: int = 10,
                  page_number: int = 1) -> FilmsList | None:
        sorting = [{"title.raw": "asc"}]
        if sort:
            match sort:
                case "imdb_rating":
                    sorting.insert(0, {"imdb_rating": "asc"})
                case "-imdb_rating":
                    sorting.insert(0, {"imdb_rating": "desc"})

        query = None
        if filter_genre:
            query = {
                "nested": {
                    "path": "genre",
                    "query": {
                        "term": {"genre.id": filter_genre}
                    }
                }
            }

        docs = await self._get_from_elastic(query=query, sort=sorting, size=size, page_number=page_number)
        if not docs:
            return None

        return FilmsList(
            count=docs['hits']['total']['value'],
            results=[Film(**doc['_source']) for doc in docs['hits']['hits']]
        )


@lru_cache()
def get_film_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(elastic)
