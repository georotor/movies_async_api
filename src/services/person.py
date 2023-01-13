from uuid import UUID
from functools import lru_cache
from operator import itemgetter

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from models.person import Person
from services.node import NodeService


class PersonService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = Person
        self.index = 'persons'

    """У персоны часть данных лежит в другом индексе, поэтому подменяем метод базового класса."""
    async def get_by_id(self, person_id: UUID) -> Person | None:
        person = await super().get_by_id(person_id)
        if not person:
            return None

        movies = await self.get_movies_with_person(person_id)
        if not movies:
            return person

        roles = {}
        for movie in movies['hits']['hits']:
            for role in ("actors", "writers", "directors"):
                if str(person_id) in map(itemgetter('id'), movie['_source'][role]):
                    if role not in roles:
                        roles[role] = []
                    roles[role].append(movie['_source']['id'])

        if bool(roles):
            person.roles = roles

        return person

    async def get_movies_with_person(self, person_id: UUID) -> list[dict[str, ...]] | None:
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

        movies = await self._get_from_elastic(index="movies", query=query, size=1000)

        return movies


@lru_cache()
def get_person_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(elastic)
