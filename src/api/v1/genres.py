from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.genre import GenreService, get_genre_service

router = APIRouter()


class Genre(BaseModel):
    id: UUID
    name: str
    films_count: int
    description: str


class GenreShort(BaseModel):
    id: UUID
    name: str


class GenresList(BaseModel):
    count: int
    results: list[GenreShort]


@router.get('/', response_model=GenresList, description="Постраничный список жанров.")
async def genres_get(
        page_size: int = Query(default=50, alias="page[size]", ge=10, le=200),
        page_number: int = Query(default=1, alias="page[number]", ge=1),
        genre_service: GenreService = Depends(get_genre_service)
) -> GenresList:

    genres = await genre_service.get(size=page_size, page_number=page_number)
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genres not found')

    return GenresList(**genres.dict())


@router.get('/{genre_id}', response_model=Genre, description="Детальная информация по жанру.")
async def genre_details(genre_id: UUID, genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')

    return Genre(**genre.dict())
