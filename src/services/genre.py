from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from cache.pydantic_cache import pydantic_cache
from db.elastic import get_elastic
from db_managers.abstract_manager import AbstractDBManager
from db_managers.es_manager import ESDBManager
from elastic_requests.bool_query import must_query_factory
from models.genre import Genre, GenresList
from services.node import NodeService


class GenreService(NodeService):
    """Логика для обработки запросов со стороны API."""
    def __init__(self, db_manager: AbstractDBManager):
        super().__init__(db_manager)
        self.Node = Genre
        self.index = 'genres'

    @pydantic_cache(model=GenresList)
    async def get_genres(
            self, size: int = 10, page_number: int = 1
    ) -> GenresList | None:
        """Метод для получения списка жанров. Пока без дополнительных изысков.

        Args:
          size: кол-во записей на странице (limit);
          page_number: номер страницы.

        """
        query_obj = must_query_factory(
            size=size, page_number=page_number, sort='name.raw'
        )

        models, total, search_after = await self._get_from_elastic(
            query=query_obj.body,
        )

        if not models:
            return None

        return GenresList(count=total, results=models)


@lru_cache()
def get_genre_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    es_db_manager = ESDBManager(elastic)
    return GenreService(es_db_manager)
