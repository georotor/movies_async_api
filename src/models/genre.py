from uuid import UUID

from models.node import Node


class Genre(Node):
    id: UUID
    name: str
    films_count: int
    description: str


class GenresList(Node):
    count: int
    results: list[Genre]
