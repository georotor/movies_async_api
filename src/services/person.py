from models.person import Person
from services.node import NodeService

from uuid import UUID
from operator import itemgetter

from functools import lru_cache
from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends


from db.elastic import get_elastic
from db.redis import get_redis


class PersonService(NodeService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        super().__init__(redis, elastic)
        self.Node = Person
        self.index = 'persons'

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
        # Ищем кинопроизведения с участием данной персоны
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
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
