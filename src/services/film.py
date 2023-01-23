from functools import lru_cache

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from models.film import Film, FilmsList
from services.node import NodeService


from enum import Enum


class SortField(str, Enum):
    IMDB_RATING = "imdb_rating"


class FilmService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = Film
        self.index = 'movies'

    async def get_films(
        self,
        sort_field=SortField.IMDB_RATING,
        sort_order="desc",
        genre=None,
        per_page=50,
        search_after=None,
    ) -> tuple[list[Film], str] | None:
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
