import binascii
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from orjson import JSONDecodeError

from api.v1.films import Film
from models.node import Node
from services.person import PersonService, get_person_service


router = APIRouter()


class Roles(Node):
    actor: list[UUID]
    writer: list[UUID]
    director: list[UUID]


class Person(Node):
    id: UUID
    name: str


class PersonDetails(Person):
    roles: Roles


class PersonsResult(Node):
    count: int
    next: str | None
    results: list[Person]


class FilmsResult(Node):
    count: int
    results: list[Film]


@router.get("/search", response_model=PersonsResult)
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

    return PersonsResult(**dict(persons))


@router.get("/{person_id}/film", response_model=FilmsResult, description="Список всех фильмов с персоной.")
async def get_person_films(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> FilmsResult:
    movies = await person_service.get_movies_with_person(person_id)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmsResult(**dict(movies))


@router.get("/{person_id}", response_model=PersonDetails, description="Детальная информация по персоне.")
async def get_person_details(
    person_id: UUID, person_service: PersonService = Depends(get_person_service)
) -> PersonDetails:

    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="person not found")

    return PersonDetails(**dict(person))


@router.get("", response_model=PersonsResult)
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

    return PersonsResult(**dict(persons))

