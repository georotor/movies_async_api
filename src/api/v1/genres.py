from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from .schemes import GenreDetails, GenresList
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get(
    "/{genre_id}",
    response_model=GenreDetails,
    summary='Информация о жанре',
    description='Получение данных о жанре по id'
)
async def get_genre_details(
    genre_id: UUID,
    genre_service: GenreService = Depends(get_genre_service)
) -> GenreDetails:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")

    return GenreDetails(**dict(genre))


@router.get(
    "",
    response_model=GenresList,
    summary='Список жанров',
    description='Список жанров с поддержкой пагинации'
)
async def get_genres(
    page_size: int = Query(default=10, alias="page[size]", ge=10, le=100),
    page_number: int = Query(default=1, alias="page[number]", ge=1),
    genre_service: GenreService = Depends(get_genre_service),
) -> GenresList:
    genres = await genre_service.get_genres(size=page_size, page_number=page_number)
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")
    return GenresList(**dict(genres))
