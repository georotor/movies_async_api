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


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


from services.base import BaseService
from pydantic import BaseModel


class FilmService(BaseService):
    def __init__(self, elastic: AsyncElasticsearch, model: BaseModel, index: str):
        super().__init__(elastic=elastic)
        self.model = model
        self.index = index

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await super().get_by_id(id_=film_id)
        return film

    async def get_films(
        self,
        sort_field=SortField.IMDB_RATING,
        sort_order=SortOrder.DESC,
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

        films = await super().get_list(
            query=query,
            search_after=search_after,
        )
        return films

    async def search(self, query, per_page, search_after) -> tuple[list[Film], str]:
        query = {
            "size": per_page,
            "query": {
                "multi_match": {"query": query, "fields": ["title^3", "description"]}
            },
            "sort": {"imdb_rating": "desc", "id": "desc"},
        }
        result = await super().search(query=query, search_after=search_after)
        return result


@lru_cache()
def get_film_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(elastic, index="movies", model=Film)
