from uuid import UUID
from functools import lru_cache
from operator import itemgetter

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from models.person import Person, PersonsList
from models.film import Film, FilmsList
from services.node import NodeService


class PersonService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = Person
        self.index = 'persons'

    async def search(self, query: str, page_number=1, size=10) -> PersonsList | None:
        _query = {
            "query_string": {
                "query": query
            }
        }

        docs = await self._get_from_elastic(query=_query, size=size, page_number=page_number)
        if not docs:
            return None

        person_list = PersonsList(
            count=docs['hits']['total']['value'],
            results=[]
        )

        for doc in docs['hits']['hits']:
            person = Person(**doc['_source'])
            person = await self.get_person_with_movies(person)
            person_list.results.append(person)

        return person_list

    """У персоны часть данных лежит в другом индексе, поэтому подменяем метод базового класса."""
    async def get_by_id(self, person_id: UUID) -> Person | None:
        person = await super().get_by_id(person_id)
        if not person:
            return None

        return await self.get_person_with_movies(person)

    async def get_person_with_movies(self, person: Person) -> Person:
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

    async def _get_movies_with_person(self, person_id: UUID) -> list[dict[str, ...]] | None:
        # Ищем все кинопроизведения с участием данной персоны во всех ролях
        query = {"bool": {"should": []}}
        for role in ("actors", "writers", "directors"):
            query["bool"]["should"].append({
                "nested": {
                    "query": {
                        "term": {f"{role}.id": person_id}
                    },
                    "path": role
                }
            })

        return await self._get_from_elastic(index="movies", query=query, size=1000)


@lru_cache()
def get_person_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(elastic)
