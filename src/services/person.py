from functools import lru_cache
from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from cache.pydantic_cache import pydantic_cache
from db.elastic import get_elastic
from db_managers.abstract_manager import AbstractDBManager
from db_managers.es_manager import ESDBManager
from elastic_requests.bool_query import BoolQuery, must_query_factory
from models.film import Film, FilmsList
from models.person import PersonDetails, PersonsList, Roles
from services.node import NodeService


class PersonService(NodeService):
    """Логика для обработки запросов со стороны API. Основная проблема - не
    оптимальная структура данных в Elastic, при которой данные о персоне
    разбросаны по нескольким индексам.

    В прошлой версии кода метод get_by_id базового класса был переопределен.
    После получения документа с данными о персоне выполнялся дополнительный
    запрос в индекс с фильмами. Таким образом заполнялась информация о ролях.

    Это не самое очевидное поведение - вместо одного ожидаемого запроса в БД
    выполняется сразу несколько, даже когда никакая дополнительная информация
    о персоне не требуется.

    Если в будущем окажется, что эта информация нужна всегда - стоит просто
    добавить ее в индекс персон в Elastic.

    """
    def __init__(self, db_manager: AbstractDBManager):
        super().__init__(db_manager)
        self.Node = PersonDetails
        self.index = 'persons'

    async def get_person_details(
            self, person_id: UUID
    ) -> Optional[PersonDetails]:
        person = await self.get_by_id(person_id)
        if not person:
            return None

        roles = Roles.schema()['properties']
        films = await self._get_films(roles, person_id)
        person.roles = self._extract_roles(films, roles, person_id)
        return person

    async def _get_films(
            self, roles: list, person_id: UUID
    ) -> list[Optional[Film]]:
        """Получаем список фильмов, связанных с указанной персоной. Так как
        искать приходиться сразу по нескольким категориям (у персоны могут быть
        разные роли), то используем BoolQuery с boolean_clause='should'.

        Args:
          roles: список ролей персоны по которым будет производиться поиск;
          person_id: уникальный идентификатор персоны.

        """
        query = BoolQuery(boolean_clause='should')
        query.add_pagination(page_number=1, size=10000)
        for role in roles:
            query.insert_nested_query(person_id, '{}s'.format(role), 'id')
        films, _, _ = await self.db_manager.search_all(
            'movies', Film, query.body
        )
        return films

    @staticmethod
    def _extract_roles(
            films: [Optional[Film]], roles: list, person_id
    ) -> Roles:
        """Заполняем модель Roles, разбивая список фильмов по ролям персоны.

        Args:
          films: список фильмов;
          roles: список интересующих ролей.

        """
        roles_data = {}
        for film in films:
            for role in roles:
                staff = film.dict()['{}s'.format(role)]
                if person_id in [man['id'] for man in staff]:
                    roles_data.setdefault(role, set()).add(film.id)
        return Roles(**roles_data)

    @pydantic_cache(model=FilmsList)
    async def get_movies_with_person(
            self, person_id: UUID
    ) -> Optional[FilmsList]:
        """Поиск фильмов в которых участвовала персона.

        Args:
          person_id: уникальный идентификатор персоны.

        """
        roles = Roles.schema()['properties']
        movies = await self._get_films(roles, person_id)
        if not movies:
            return None

        return FilmsList(
            count=len(movies),
            results=movies
        )

    @pydantic_cache(model=PersonsList)
    async def get_persons(
            self,
            size: int = 50,
            search_after: Optional[list] = None,
    ) -> Optional[PersonsList]:
        """Метод для получения списка персон. В сортировке указываем основное
        поле ('name.raw'), дополнительная сортировка по id буде добавлена
        фабрикой.

        Args:
          size: кол-во записей на странице (limit);
          search_after: стартовое значение для следующей выдачи, не работает
            без sort.

        """

        query_obj = must_query_factory(
            size=size, search_after=search_after, sort='name.raw'
        )

        models, total, search_after = await self._get_from_elastic(
            query=query_obj.body,
        )

        if not models:
            return None

        return PersonsList(
            count=total,
            next=await self.b64encode(search_after),
            results=models
        )

    @pydantic_cache(model=PersonsList)
    async def search(
            self,
            search: str,
            size: int = 10,
            search_after: Optional[list] = None,
            sort: str = '',
            page_number: int = 1
    ) -> Optional[PersonsList]:
        """Метод для поиска персоны по ключевому слову.

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
        models, total, search_after = await self._get_from_elastic(
            query_obj.body
        )
        if not models:
            return None

        return PersonsList(
            count=total,
            next=await self.b64encode(search_after),
            results=models
        )


@lru_cache()
def get_person_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    es_db_manager = ESDBManager(elastic)
    return PersonService(es_db_manager)
