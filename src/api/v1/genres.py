from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.genre import GenreService, get_genre_service

router = APIRouter()


class Genre(BaseModel):
    id: UUID
    name: str


class Result(BaseModel):
    result: list[Genre]
    next_page: str


@router.get("/search", response_model=Result)
async def get_genres(
    query: str = Query(default=..., min_length=3),
    search_after: str = Query(default=None, alias="page[next]"),
    genre_service: GenreService = Depends(get_genre_service),
):
    genres, search_after = await genre_service.search(query, search_after=search_after)
    if not genres:
        return Result(result=[], next_page=search_after)
    return Result(result=genres, next_page=search_after)


@router.get("/{genre_id}", response_model=Genre)
async def get_person_details(
    genre_id: str, genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")

    return Genre(**genre.dict())


@router.get("", response_model=Result)
async def get_genres(
    genre_service: GenreService = Depends(get_genre_service),
    search_after: str = Query(default=None, alias="page[next]"),
):
    genres, search_after = await genre_service.get_genres(search_after=search_after)
    if not genres:
        return Result(result=[], next_page=search_after)
    return Result(result=genres, next_page=search_after)
