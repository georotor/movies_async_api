import json
from typing import Literal

from pydantic import BaseModel
from pydantic.types import PositiveInt


class Page(BaseModel):
    """Данные для пагинации. В ES используются поля "from" (сколько данных
    пропустить) и "size" (сколько данных выдать). Но нам вероятнее всего будет
    удобнее оперировать номерами страниц.

    """
    size: PositiveInt = 50
    number: PositiveInt = 1


class Sort(BaseModel):
    """ES поддерживает несколько опций сортировки. Пока ограничимся минимальным
    набором - имя поля и порядок сортировки.

    """
    field: str
    order: Literal['asc', 'desc']


def sort_factory(sort: str):
    """Фабрика для создания объекта сортировки. Сортировка указана в django
    стиле: название поля с опциональным знаком '-', который означает сортировку
    в обратном порядке.

    Пример: sort='name' / sort='-name'

    """
    order = 'desc' if sort.startswith('-') else 'asc'
    field = sort.lstrip('-')
    return Sort(field=field, order=order)


def page_factory(size, page=1):
    """Фабрика для создания объекта пагинации. """
    return Page(size=size, number=page)


def create_curl_string(query_body, index):
    """Создание строки с запросом для curl на основе объекта query_body.
    Полезно для теста и не только.

    """
    url = 'http://127.0.0.1:9200/{}/_search'.format(index)
    template = "curl -XGET {} -H 'Content-Type: application/json' -d'{}'"
    return template.format(url, json.dumps(query_body))