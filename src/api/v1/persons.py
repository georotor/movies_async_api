from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.person import PersonService, get_person_service
from api.v1.films import Film

router = APIRouter()


class Person(BaseModel):
    id: UUID
    name: str


class Result(BaseModel):
    next_page: str
    result: list[Person]


@router.get("/search", response_model=Result)
async def get_persons(
    query: str = Query(default=..., min_length=3),
    per_page: int = Query(default=50, ge=10, le=100),
    search_after: str = Query(default=None, alias="page[next]"),
    person_service: PersonService = Depends(get_person_service),
):
    persons, search_after = await person_service.search(query, per_page, search_after)
    if not persons:
        return Result(next_page=search_after, result=[])
    return Result(next_page=search_after, result=persons)


class FilmResult(BaseModel):
    next_page: str
    films: list[Film]


@router.get("/{person_id}/film", response_model=FilmResult)
async def get_person_films(
    person_id: UUID,
    person_service: PersonService = Depends(get_person_service),
    per_page: int = Query(default=50, ge=10, le=100),
    search_after: str = Query(default=None, alias="page[next]"),
):
    films, search_after = await person_service.get_person_films(
        person_id, per_page, search_after
    )
    if not films:
        return FilmResult(next_page=search_after, films=[])
    return FilmResult(next_page=search_after, films=films)


@router.get("/{person_id}", response_model=Person)
async def get_person_details(
    person_id: UUID, person_service: PersonService = Depends(get_person_service)
) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="person not found")

    return Person(**person.dict())


@router.get("", response_model=Result)
async def get_persons(
    per_page: int = Query(default=50, ge=10, le=100),
    search_after: str = Query(default=None, alias="page[next]"),
    person_service: PersonService = Depends(get_person_service),
):
    persons, search_after = await person_service.get_persons(
        per_page=per_page, search_after=search_after
    )
    if not persons:
        return Result(next_page=search_after, result=[])
    return Result(next_page=search_after, result=persons)
