"""Модуль для работы с запросами типа Match. Пример запроса:

    {"query":
        {"match":
            {"": {"": ""}}},
        "sort":
            {"": {"order": ""}
        },
        "from": 0,
        "size": 1
    }

"""

from typing import Any, Optional

from pydantic import BaseModel

from src.services.elastic_requests.general_options import (Page, Sort,
                                                           page_factory,
                                                           sort_factory,
                                                           create_curl_string)


class MatchQueryRule(BaseModel):
    field: str
    query: str
    fuzziness: str = 'auto'


class MatchQueryBody(BaseModel):
    match: Optional[MatchQueryRule]
    sort: Optional[Sort]
    page: Optional[Page]


def create_match_rule(data: dict, model) -> list:
    """Принимает на вход словарь, отдает список объектов MatchQueryRule.
    Так как match не поддерживает поиск по нескольким полям, игнорируем все
    кроме первой пары ключ / значение.

    """
    for field, value in data.items():
        return model(field=field, query=value)


def match_simple_factory(
    match: dict = None,
    sort: str = None,
    size: int = None,
    page: int = None,
) -> MatchQueryBody:
    """Создает объект класса MatchQueryBody. Сейчас логика довольна линейна, в
    будущем разных типов запросов может стать больше. Сюда же можно будет
    добавить дополнительную валидацию.

    Сортировка по одному полю, с указанием порядка (desc / asc).
    Указание параметра fuzziness в словаре match не предполагается.

    """
    match_body_obj = MatchQueryBody(
        match=match and create_match_rule(match, MatchQueryRule),
        sort=sort and sort_factory(sort),
        page=size and page_factory(size, page or 1),
    )
    return match_body_obj


def update_match_query(match_query, match_obj):
    match_query.update(
        {match_obj.field: {"query": match_obj.query}},
    )


def create_match_query(match_obj) -> dict[str, Any]:
    """Нужно сформировать тело запроса из объекта MatchQueryBody.
    1) Сформировать match запрос из объекта MatchQueryRule
    2) Сформировать значения "from" и "size" из объекта Page
    3) Сформировать значения "sort" из объекта Sort

    """
    match_query = {}
    query_body = {"query": {"match": match_query}}

    if match_obj.match:
        update_match_query(match_query, match_obj.match)

    if match_obj.sort:
        query_body["sort"] = {
            match_obj.sort.field: {"order": match_obj.sort.order}
        }

    if match_obj.page:
        query_body["from"] = (match_obj.page.number - 1) * match_obj.page.size
        query_body["size"] = match_obj.page.size

    return query_body


if __name__ == '__main__':
    import logging

    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    quary_obj = match_simple_factory(
        {'title': 'Star-ving'}, sort='-imdb_rating', size=10, page=1,
    )
    quary_body = create_match_query(quary_obj)
    logger.info(create_curl_string(quary_body, 'movies'))