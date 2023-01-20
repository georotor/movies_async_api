from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.person import PersonService, get_person_service

router = APIRouter()


class Person(BaseModel):
    id: UUID
    name: str


@router.get("/search", response_model=list[Person])
async def get_persons(
    query: str = Query(default=..., min_length=3),
    person_service: PersonService = Depends(get_person_service),
):
    persons = await person_service.search(query)
    if not persons:
        return []
    return persons


@router.get("/{person_id}", response_model=Person)
async def get_person_details(
    person_id: UUID, person_service: PersonService = Depends(get_person_service)
) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="person not found")

    return Person(**person.dict())


@router.get("", response_model=list[Person])
async def get_persons(
    page: int = 1,
    per_page: int = 50,
    person_service: PersonService = Depends(get_person_service),
):
    persons = await person_service.get_persons(
        page=page,
        per_page=per_page,
    )
    if not persons:
        return []
    return persons
