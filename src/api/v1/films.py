import binascii
from enum import Enum
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from orjson import JSONDecodeError

from models.node import Node
from services.film import FilmService, get_film_service

router = APIRouter()


class Genre(Node):
    id: UUID
    name: str


class Person(Node):
    id: UUID
    name: str


class Film(Node):
    id: str
    title: str
    imdb_rating: float


class FilmDetails(Film):
    description: str
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]


class FilmsList(Node):
    count: int
    next: str | None
    results: list[Film]


class FilmsSorting(str, Enum):
    asc = "imdb_rating"
    desc = "-imdb_rating"


@router.get("/search", response_model=FilmsList)
async def get_films(
        search: str = Query(default=..., min_length=3),
        page_size: int = Query(default=10, alias="page[size]", ge=10, le=100),
        page_number: int = Query(
            default=1,
            alias="page[number]",
            ge=1,
            description="Номер страницы, данным перебором можно получить не более 10000 документов"
        ),
        page_next: str | None = Query(
            default=None,
            alias="page[next]",
            description="Токен (next) для получения следующей страницы, при использовании игнорируется page[number]"
        ),
        film_service: FilmService = Depends(get_film_service),
) -> FilmsList:
    search_after = None
    if page_next:
        try:
            search_after = await film_service.b64decode(page_next)
        except (binascii.Error, JSONDecodeError):
            raise HTTPException(status_code=422, detail="page[next] not valid")

    movies = await film_service.search(search=search, search_after=search_after, page_number=page_number, size=page_size)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmsList(**dict(movies))


@router.get("/{film_id}", response_model=FilmDetails)
async def film_details(
        film_id: UUID, film_service: FilmService = Depends(get_film_service)
) -> FilmDetails:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return FilmDetails(**dict(film))


@router.get("", response_model=FilmsList)
async def get_films(
        sort: FilmsSorting | None = None,
        filter_genre: UUID | None = Query(default=None, alias="filter[genre]"),
        page_size: int = Query(default=10, alias="page[size]", ge=10, le=100),
        page_number: int = Query(
            default=1,
            alias="page[number]",
            ge=1,
            description="Номер страницы, данным перебором можно получить не более 10000 документов"
        ),
        page_next: str | None = Query(
            default=None,
            alias="page[next]",
            description="Токен (next) для получения следующей страницы, при использовании игнорируется page[number]"
        ),
        film_service: FilmService = Depends(get_film_service),
) -> FilmsList:
    search_after = None
    if page_next:
        try:
            search_after = await film_service.b64decode(page_next)
        except (binascii.Error, JSONDecodeError):
            raise HTTPException(status_code=422, detail="page[next] not valid")

    movies = await film_service.get_films(sort=sort, search_after=search_after, filter_genre=filter_genre,
                                          size=page_size, page_number=page_number)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmsList(**dict(movies))
