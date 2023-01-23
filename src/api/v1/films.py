import binascii
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from orjson import JSONDecodeError

from services.film import FilmService, get_film_service

router = APIRouter()


class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float


class Genre(BaseModel):
    id: UUID
    name: str


class Person(BaseModel):
    id: UUID
    name: str


class FilmDetails(BaseModel):
    id: UUID
    title: str
    imdb_rating: float
    description: str
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]


class Result(BaseModel):
    next_page: str
    result: list[Film]


class FilmsList(BaseModel):
    count: int
    next: str | None
    results: list[Film]


@router.get("/search", response_model=FilmsList)
async def get_films(
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
    film_service: FilmService = Depends(get_film_service),
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


@router.get("/{film_id}", response_model=FilmDetails)
async def film_details(
    film_id: UUID, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return FilmDetails(**film.dict())


@router.get("", response_model=Result)
async def get_films(
    genre: str = None,
    # page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=10, le=100),
    sort_field: str = "imdb_rating",
    sort_order: str = "desc",
    search_after: str = Query(default=None, alias="page[next]"),
    film_service: FilmService = Depends(get_film_service),
):
    films, search_after = await film_service.get_films(
        sort_field=sort_field,
        sort_order=sort_order,
        genre=genre,
        per_page=per_page,
        search_after=search_after,
    )
    if not films:
        return []
    films = [
        Film(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]
    return Result(next_page=search_after, result=films)
