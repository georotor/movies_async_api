from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

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


@router.get("/search", response_model=list[Film])
async def get_films(
    query: str = Query(default=..., min_length=3),
    film_service: FilmService = Depends(get_film_service),
):
    films = await film_service.search(query)
    if not films:
        return []
    return [
        Film(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]


@router.get("/{film_id}", response_model=FilmDetails)
async def film_details(
    film_id: UUID, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return FilmDetails(**film.dict())


@router.get("", response_model=list[Film])
async def get_films(
    genre: str,
    page: int = 1,
    per_page: int = 50,
    sort_field: str = "imdb_rating",
    sort_order: str = "desc",
    film_service: FilmService = Depends(get_film_service),
):
    films = await film_service.get_films(
        sort_field=sort_field,
        sort_order=sort_order,
        genre=genre,
        page=page,
        per_page=per_page,
    )
    if not films:
        return []
    return [
        Film(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]
