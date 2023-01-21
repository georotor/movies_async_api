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
    search_after: list
    result: list[Person]


@router.get("/search", response_model=Result)
async def get_persons(
    query: str = Query(default=..., min_length=3),
    per_page: int = Query(default=50, ge=10, le=100),
    search_after: str = None,
    person_service: PersonService = Depends(get_person_service),
):
    persons, search_after = await person_service.search(query, per_page, search_after)
    if not persons:
        return Result(search_after=search_after, result=[])
    return Result(search_after=search_after, result=persons)


@router.get("/{person_id}/film", response_model=list[Film])
async def get_person_films(
    person_id: UUID, person_service: PersonService = Depends(get_person_service)
):
    films = await person_service.get_person_films(person_id)
    if not films:
        return []
    return films


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
	search_after: str = None,
    person_service: PersonService = Depends(get_person_service),
):
    persons, search_after = await person_service.get_persons(
        per_page=per_page,
		search_after=search_after
    )
    if not persons:
        return Result(search_after=search_after, result=[])
    return Result(search_after=search_after, result=persons)
