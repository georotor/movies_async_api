import binascii
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from orjson import JSONDecodeError

from services.person import PersonService, get_person_service
from api.v1.films import Film

router = APIRouter()


class Roles(BaseModel):
    actor: list[UUID]
    writer: list[UUID]
    director: list[UUID]


class Person(BaseModel):
    id: UUID
    name: str


class PersonDetails(Person):
    roles: Roles


class Result(BaseModel):
    count: int
    next: str | None
    results: list[Person]


class FilmResult(BaseModel):
    count: int
    results: list[Film]


@router.get("/search", response_model=Result)
async def get_persons(
    query: str = Query(default=..., min_length=3),
    page_size: int = Query(default=10, alias="page[size]", ge=10, le=100),
    page_next: str = Query(default=None, alias="page[next]"),
    person_service: PersonService = Depends(get_person_service),
):

    search_after = None
    if page_next:
        try:
            search_after = await person_service.b64decode(page_next)
        except (binascii.Error, JSONDecodeError):
            raise HTTPException(status_code=422, detail="page[next] not valid")

    persons = await person_service.search(query=query, size=page_size, search_after=search_after)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='persons not found')

    return Result(**persons.dict())


@router.get("/{person_id}/film", response_model=FilmResult, description="Список всех фильмов с персоной.")
async def get_person_films(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> FilmResult:
    movies = await person_service.get_movies_with_person(person_id)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmResult(**movies.dict())


@router.get("/{person_id}", response_model=PersonDetails, description="Детальная информация по персоне.")
async def get_person_details(
    person_id: UUID, person_service: PersonService = Depends(get_person_service)
) -> PersonDetails:

    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="person not found")

    return PersonDetails(**person.dict())


@router.get("", response_model=Result)
async def get_persons(
    page_size: int = Query(default=50, ge=10, le=100, alias="page[size]"),
    page_next: str = Query(default=None, alias="page[next]"),
    person_service: PersonService = Depends(get_person_service),
):

    search_after = None
    if page_next:
        try:
            search_after = await person_service.b64decode(page_next)
        except (binascii.Error, JSONDecodeError):
            raise HTTPException(status_code=422, detail="page[next] not valid")

    persons = await person_service.get_persons(size=page_size, search_after=search_after)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='persons not found')

    return Result(**persons.dict())

