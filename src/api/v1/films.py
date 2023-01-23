import binascii
from enum import Enum
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from orjson import JSONDecodeError

from services.film import FilmService, get_film_service

router = APIRouter()


class GenreShort(BaseModel):
    id: UUID
    name: str


class PersonShort(BaseModel):
    id: UUID
    name: str


class FilmShort(BaseModel):
    id: UUID
    title: str
    imdb_rating: float


class Film(BaseModel):
    id: UUID
    title: str
    imdb_rating: float
    description: str
    genre: list[GenreShort]
    actors: list[PersonShort]
    writers: list[PersonShort]
    directors: list[PersonShort]


class FilmsList(BaseModel):
    count: int
    next: str | None
    results: list[FilmShort]


class FilmsSorting(str, Enum):
    asc = "imdb_rating"
    desc = "-imdb_rating"


@router.get('/search/', response_model=FilmsList, description="Поиск по фильмам.")
async def films_search(
        query: str = Query(default=..., min_length=3),
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
        film_service: FilmService = Depends(get_film_service)
) -> FilmsList:

    search_after = None
    if page_next:
        try:
            search_after = await film_service.b64decode(page_next)
        except (binascii.Error, JSONDecodeError):
            raise HTTPException(status_code=422, detail="page[next] not valid")

    movies = await film_service.search(query=query, search_after=search_after, page_number=page_number, size=page_size)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmsList(**movies.dict())


@router.get('/{film_id}', response_model=Film, description="Детальная информация по фильму.")
async def film_details(film_id: UUID, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return Film(**film.dict())


@router.get('/', response_model=FilmsList, description="Постраничный список фильмов.")
async def films(
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
        film_service: FilmService = Depends(get_film_service)
) -> FilmsList:

    search_after = None
    if page_next:
        try:
            search_after = await film_service.b64decode(page_next)
        except (binascii.Error, JSONDecodeError):
            raise HTTPException(status_code=422, detail="page[next] not valid")

    movies = await film_service.get(sort=sort, search_after=search_after, filter_genre=filter_genre,
                                    size=page_size, page_number=page_number)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmsList(**movies.dict())
