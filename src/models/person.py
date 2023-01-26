from uuid import UUID

from pydantic import Field

from models.node import Node


class Roles(Node):
    actor: list[UUID] = []
    writer: list[UUID] = []
    director: list[UUID] = []

    def __getitem__(self, item):
        return getattr(self, item)


class Person(Node):
    id: UUID
    name: str


class PersonDetails(Person, Node):
    roles: Roles = Field(default_factory=Roles)


class PersonsList(Node):
    count: int
    next: str | None
    results: list[Person]
