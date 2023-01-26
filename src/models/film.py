from uuid import UUID

from models.node import Node


class Genre(Node):
    id: UUID
    name: str


class Person(Node):
    id: UUID
    name: str


class Film(Node):
    id: str
    title: str
    imdb_rating: float
    description: str
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]


class FilmsList(Node):
    count: int
    next: str | None
    results: list[Film]
