from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from models.film import Film
from services.node import NodeService


class FilmService(NodeService):
    def __init__(self, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.Node = Film
        self.index = 'movies'


@lru_cache()
def get_film_service(
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(elastic)
