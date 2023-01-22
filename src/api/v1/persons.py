from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.v1.films import FilmsList
from services.person import PersonService, get_person_service


router = APIRouter()


class Roles(BaseModel):
    actor: list[UUID]
    writer: list[UUID]
    director: list[UUID]


class Person(BaseModel):
    id: UUID
    name: str
    roles: Roles


class PersonsList(BaseModel):
    count: int
    results: list[Person]


@router.get('/search/', response_model=PersonsList, description="Поиск персон.")
async def persons_search(
        query: str = Query(default=..., min_length=3),
        page_size: int = Query(default=10, alias="page[size]", ge=10, le=100),
        page_number: int = Query(default=1, alias="page[number]", ge=1, le=50),
        person_service: PersonService = Depends(get_person_service)
) -> PersonsList:

    persons = await person_service.search(query=query, page_number=page_number, size=page_size)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='persons not found')

    return PersonsList(**persons.dict())


@router.get('/{person_id}/film', response_model=FilmsList, description="Список всех фильмов с персоной.")
async def person_films(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> FilmsList:
    movies = await person_service.get_movies_with_person(person_id)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return FilmsList(**movies.dict())


@router.get('/{person_id}', response_model=Person, description="Детальная информация по персоне.")
async def person_details(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return person
