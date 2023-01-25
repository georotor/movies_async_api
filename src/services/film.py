from functools import lru_cache
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from fastapi_cache.decorator import cache

from db.elastic import get_elastic
from models.film import Film, FilmsList
from services.node import NodeService


class FilmService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = Film
        self.index = 'movies'

    @cache()
    async def get_films(self, sort: str | None, search_after: list | None = None,
                        filter_genre: UUID | None = None, size: int = 10, page_number: int = 1) -> FilmsList | None:
        _sort = [
            {"title.raw": "asc"},
            {"id": "asc"}
        ]
        if sort:
            match sort:
                case "imdb_rating":
                    _sort.insert(0, {"imdb_rating": "asc"})
                case "-imdb_rating":
                    _sort.insert(0, {"imdb_rating": "desc"})

        query = None
        if filter_genre:
            query = {
                "nested": {"query": {"term": {"genre.id": filter_genre}}, "path": "genre"}
            }

        docs = await self._get_from_elastic(query=query, search_after=search_after,
                                            sort=_sort, size=size, page_number=page_number)
        if not docs:
            return None

        return FilmsList(
            count=docs['hits']['total']['value'],
            next=await self.b64encode(docs['hits']['hits'][-1]["sort"]) if len(docs['hits']['hits']) == size else None,
            results=[Film(**doc['_source']) for doc in docs['hits']['hits']]
        )

    @cache()
    async def search(self, query: str, search_after: list | None = None, page_number=1, size=10) -> FilmsList | None:
        _query = {
            "bool": {
                "should": [
                    {"query_string": {"query": query}},
                    {"match": {"title": query}}
                ]
            }
        }

        _sort = [
            {"_score": {"order": "desc"}},
            {"id": {"order": "asc"}}
        ]

        docs = await self._get_from_elastic(query=_query, search_after=search_after,
                                            sort=_sort, size=size, page_number=page_number)
        if not docs:
            return None

        return FilmsList(
            count=docs['hits']['total']['value'],
            next=await self.b64encode(docs['hits']['hits'][-1]["sort"]) if len(docs['hits']['hits']) == size else None,
            results=[Film(**doc['_source']) for doc in docs['hits']['hits']]
        )


@lru_cache()
def get_film_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(elastic)
