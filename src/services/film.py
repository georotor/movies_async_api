from functools import lru_cache
from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from fastapi_cache.decorator import cache

from db.elastic import get_elastic
from db_managers.abstract_manager import AbstractDBManager
from db_managers.es_manager import ESDBManager
from elastic_requests.bool_query import must_query_factory
from models.film import Film, FilmsList
from services.node import NodeService


class FilmService(NodeService):
    """Логика для обработки запросов со стороны API. Сейчас здесь есть два
    очень похожих метода: get_films и search. Оба получает примерно одинаковый
    набор данных, передают их в одну и туже фабрику и выполняют запрос в БД
    через self._get_from_elastic.

    Но несмотря на схожий код, они решают разные бизнес задачи и в будущем
    могут изменяться независимо друг от друга. Например, использовать разные
    реализации AbstractQuery для создания запросов с четким и нечетким поиском.

    """
    def __init__(self, db_manager: AbstractDBManager):
        super().__init__(db_manager)
        self.Node = Film
        self.index = 'movies'

    @cache()
    async def get_films(
            self,
            sort: str = '',
            search_after: Optional[list] = None,
            filter_genre: Optional[UUID] = None,
            size: int = 10,
            page_number: int = 1
    ) -> Optional[FilmsList]:
        """Метод для поиска похожих фильмов для рекомендаций пользователю.
        В настоящий момент смотрит только на жанр. В будущем можно добавить
        еще и поиск по актерам, заменив must на should.

        Args:
          sort: строка с указанием поля сортировки: минус в начале строки
            указывает на обратный порядок сортировки, пр. '-imdb_rating';
          search_after: стартовое значение для следующей выдачи, не работает
            без sort;
          filter_genre: id жанра для поиска похожих фильмов;
          size: кол-во записей на странице (limit);
          page_number: номер страницы.

        """

        if filter_genre:
            related_data = {'genre.id': filter_genre}

        query_obj = must_query_factory(
            search_after=search_after,
            sort=sort,
            size=size,
            page_number=page_number,
            related_search=related_data,
        )

        models, search_after = await self._get_from_elastic(
            query=query_obj.body,
        )

        if not models:
            return None

        return FilmsList(
            count=len(models),
            next=await self.b64encode(search_after),
            results=models
        )

    @cache()
    async def search(
            self,
            search: str,
            sort: str = '',
            search_after: Optional[list] = None,
            size: int = 10,
            page_number: int = 1
    ) -> Optional[FilmsList]:
        """Метод для поиска фильма по ключевому слову.

        Args:
          search: строка с данными для поиска;
          sort: строка с указанием поля сортировки: минус в начале строки
            указывает на обратный порядок сортировки, пр. '-imdb_rating';
          search_after: стартовое значение для следующей выдачи, не работает
            без sort;
          size: кол-во записей на странице (limit);
          page_number: номер страницы.

        """
        query_obj = must_query_factory(
            search=search,
            search_after=search_after,
            sort=sort,
            size=size,
            page_number=page_number,
        )

        models, search_after = await self._get_from_elastic(query_obj.body)
        if not models:
            return None

        return FilmsList(
            count=len(models),
            next=await self.b64encode(search_after),
            results=models
        )


@lru_cache()
def get_film_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    es_db_manager = ESDBManager(elastic)
    return FilmService(es_db_manager)
