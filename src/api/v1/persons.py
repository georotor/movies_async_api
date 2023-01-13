from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.v1.films import Film
from models.person import Person
from services.person import PersonService, get_person_service


router = APIRouter()


@router.get('/{person_id}/film', response_model=list[Film])
async def person_films(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> list[Film]:
    movies = await person_service.get_movies_with_person(person_id)
    if not movies:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [Film(**movie['_source']) for movie in movies['hits']['hits']]


@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return person
