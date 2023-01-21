from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.genre import GenreService, get_genre_service

router = APIRouter()


class Genre(BaseModel):
    id: UUID
    name: str


@router.get("/search", response_model=list[Genre])
async def get_genres(
    query: str = Query(default=..., min_length=3),
    genre_service: GenreService = Depends(get_genre_service),
):
    genres = await genre_service.search(query)
    if not genres:
        return []
    return genres


@router.get("/{genre_id}", response_model=Genre)
async def get_person_details(
    genre_id: str, genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")

    return Genre(**genre.dict())


@router.get("", response_model=list[Genre])
async def get_genres(
    genre_service: GenreService = Depends(get_genre_service),
):
    genres = await genre_service.get_genres()
    if not genres:
        return []
    return genres
