from enum import Enum
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.film import FilmService, get_film_service

router = APIRouter()


class Genre(BaseModel):
    id: UUID
    name: str


class Person(BaseModel):
    id: UUID
    name: str


class Film(BaseModel):
    id: UUID
    title: str
    imdb_rating: float


class FilmFull(BaseModel):
    id: UUID
    title: str
    imdb_rating: float
    description: str
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]


class FilmsList(BaseModel):
    count: int
    results: list[Film]


class FilmsSorting(str, Enum):
    asc = "imdb_rating"
    desc = "-imdb_rating"


@router.get('/search/', response_model=FilmsList)
async def films_search(
        query: str = Query(default=..., min_length=3),
        page_size: int = Query(default=10, alias="page[size]", ge=10, le=100),
        page_number: int = Query(default=1, alias="page[number]", ge=1, le=50),
        film_service: FilmService = Depends(get_film_service)
) -> FilmsList:

    movies = await film_service.search(query=query, page_number=page_number, size=page_size)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmsList(**movies.dict())


@router.get('/{film_id}', response_model=FilmFull)
async def film_details(film_id: UUID, film_service: FilmService = Depends(get_film_service)) -> FilmFull:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return FilmFull(**film.dict())


@router.get('/', response_model=FilmsList)
async def films(
        sort: FilmsSorting | None = None,
        filter_genre: UUID | None = Query(default=None, alias="filter[genre]"),
        page_size: int = Query(default=10, alias="page[size]", ge=10, le=100),
        page_number: int = Query(default=1, alias="page[number]", ge=1),
        film_service: FilmService = Depends(get_film_service)
) -> FilmsList:

    movies = await film_service.get(sort=sort, filter_genre=filter_genre, size=page_size, page_number=page_number)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmsList(**movies.dict())
