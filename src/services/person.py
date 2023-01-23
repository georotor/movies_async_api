from functools import lru_cache
from uuid import UUID
from operator import itemgetter

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from models.person import Person, PersonDetails, PersonsList
from models.film import Film, FilmsList
from services.node import NodeService


class PersonService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = PersonDetails
        self.index = 'persons'

    async def get_by_id(self, person_id: UUID) -> PersonDetails | None:
        # У персоны часть данных лежит в другом индексе, поэтому подменяем метод базового класса.
        person = await super().get_by_id(person_id)
        if not person:
            return None

        return await self.get_person_with_movies(person)

    async def get_person_with_movies(self, person: PersonDetails) -> PersonDetails:
        movies = await self._get_movies_with_person(person.id)
        if not movies:
            return person

        for movie in movies['hits']['hits']:
            for role, _ in person.roles:
                if str(person.id) in map(itemgetter('id'), movie['_source'][f"{role}s"]):
                    person.roles[role].append(movie['_source']['id'])

        return person

    async def get_movies_with_person(self, person_id: UUID) -> FilmsList | None:
        docs = await self._get_movies_with_person(person_id)
        if not docs:
            return None

        return FilmsList(
            count=docs['hits']['total']['value'],
            results=[Film(**doc['_source']) for doc in docs['hits']['hits']]
        )

    async def _get_movies_with_person(self, person_id: UUID) -> dict[str, ...] | None:
        # Ищем все кинопроизведения с участием данной персоны во всех ролях
        query = {"bool": {"should": []}}
        for role in ("actors", "writers", "directors"):
            # Собираем запрос для поиска кинопроизведений
            query["bool"]["should"].append({
                "nested": {
                    "query": {"term": {f"{role}.id": person_id}},
                    "path": role
                }
            })

        return await self._get_from_elastic(index="movies", query=query, size=1000)

    async def get_persons(self, size: int = 50, search_after: list | None = None) -> PersonsList | None:

        _sort = [
            {"name.raw": {"order": "asc"}},
            {"id": {"order": "asc"}}
        ]

        docs = await self._get_from_elastic(search_after=search_after, size=size, sort=_sort)
        if not docs:
            return None

        return PersonsList(
            count=docs['hits']['total']['value'],
            next=await self.b64encode(docs['hits']['hits'][-1]["sort"]) if len(docs['hits']['hits']) == size else None,
            results=[Person(**doc['_source']) for doc in docs['hits']['hits']]
        )

    async def search(self, query, size: int = 50, search_after: list | None = None) -> PersonsList | None:
        _query = {"match": {"name": {"query": query, "fuzziness": "AUTO"}}}

        _sort = [
            {"_score": {"order": "desc"}},
            {"id": {"order": "asc"}}
        ]

        docs = await self._get_from_elastic(query=_query, search_after=search_after, size=size, sort=_sort)
        if not docs:
            return None

        person_list = PersonsList(
            count=docs['hits']['total']['value'],
            next=await self.b64encode(docs['hits']['hits'][-1]["sort"]) if len(docs['hits']['hits']) == size else None,
            results=[Person(**doc['_source']) for doc in docs['hits']['hits']]
        )

        return person_list


@lru_cache()
def get_person_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(elastic)
