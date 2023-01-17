from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.film import FilmService, get_film_service
from dataclasses import asdict

# Объект router, в котором регистрируем обработчики
router = APIRouter()

# FastAPI в качестве моделей использует библиотеку pydantic
# https://pydantic-docs.helpmanual.io
# У неё есть встроенные механизмы валидации, сериализации и десериализации
# Также она основана на дата-классах


# Модель ответа API
class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float


class FilmDetails(BaseModel):
    id: str
    title: str
    imdb_rating: float
    description: str
    genre: list[dict]
    actors: list[dict]
    writers: list[dict]
    directors: list[dict]


@router.get("/search", response_model=list[Film])
async def get_films(query: str, film_service: FilmService = Depends(get_film_service)):
    films = await film_service.search(query)
    if not films:
        return []
    return [
        Film(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]


# С помощью декоратора регистрируем обработчик film_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру
# И адрес запроса будет выглядеть так — /api/v1/film/some_id
# В сигнатуре функции указываем тип данных, получаемый из адреса запроса (film_id: str)
# И указываем тип возвращаемого объекта — Film
# Внедряем FilmService с помощью Depends(get_film_service)
@router.get("/{film_id}", response_model=FilmDetails)
async def film_details(
    film_id: str, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum
        # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    # Перекладываем данные из models.Film в Film
    # Обратите внимание, что у модели бизнес-логики есть поле description
    # Которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и формирования ответов API
    # вы бы предоставляли клиентам данные, которые им не нужны
    # и, возможно, данные, которые опасно возвращать
    return FilmDetails(**film.dict())


@router.get("/", response_model=list[Film])
async def get_films(film_service: FilmService = Depends(get_film_service)):
    films = await film_service.get_films()
    if not films:
        return []
    return [
        Film(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]
