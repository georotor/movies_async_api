from enum import Enum
from uuid import UUID

from models.node import Node


class Genre(Node):
    id: UUID
    name: str


class GenreDetails(Genre):
    films_count: int
    description: str


class GenresList(Node):
    count: int
    results: list[Genre]


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


class Film(Node):
    id: str
    title: str
    imdb_rating: float
    length: int


class FilmDetails(Film):
    description: str
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]


class FilmsList(Node):
    count: int
    next: str | None
    results: list[Film]


class FilmsResult(Node):
    count: int
    results: list[Film]


class FilmsSorting(str, Enum):
    asc = "imdb_rating"
    desc = "-imdb_rating"
