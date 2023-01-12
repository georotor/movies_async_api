"""Модуль для работы с запросами типа Bool. Пример запроса:

    {"query":
        {"bool":
            {"must": [{"match": {"": ""}}, ]},
            {"must_not": [{"match": {"": ""}}, ]},
            {"filter": [{"match": {"": ""}}, ]},
            {"should": [{"match": {"": ""}}, ]},
        },
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


class BoolQueryRule(BaseModel):
    """Базовый класс для логических выражений, используемых в bool-запросе. """

    field: str
    value: str


class Must(BoolQueryRule):
    """Тип выражения must — возвращённые данные обязательно должны
    соответствовать правилу, которое описано в этом ключе.

    """


class MustNot(BoolQueryRule):
    """Тип выражения must_not — возвращённые данные не должны соответствовать
    правилу, описанному в этом ключе.

    """


class Filter(BoolQueryRule):
    """Тип выражения filter — похож на must, но с одним отличием. Найденные
    с помощью этих правил совпадения не будут участвовать в расчёте
    релевантности.

    """


class Should(BoolQueryRule):
    """Тип выражения should — возвращаемые данные обязательно должны
    соответствовать хотя бы одному правилу, которое описано в этом ключе.
    Он работает как ИЛИ для всех описанных внутри ключа правил.

    """


class BoolQueryBody(BaseModel):
    """Тело bool-запроса который сопоставляет документы, соответствующие
    логическим комбинациям других запросов. Он построен с использованием одного
    или нескольких логических предложений, каждое из которых имеет
    типизированное вхождение.

    """
    must: Optional[list[Must]]
    must_not: Optional[list[MustNot]]
    filter: Optional[list[Filter]]
    should: Optional[list[Should]]
    sort: Optional[Sort]
    page: Optional[Page]


def create_bool_rule(data: dict, model) -> list:
    """Принимает на вход словарь, отдает список объектов BoolQueryRule."""
    lst = []
    for field, value in data.items():
        lst.append(model(field=field, value=value))
    return lst


def bool_simple_factory(
    must: dict = None,
    must_not: dict = None,
    filter: dict = None,
    should: dict = None,
    sort: str = None,
    size: int = None,
    page: int = None,
) -> BoolQueryBody:
    """Создает объект класса BoolQueryBody. Сейчас логика довольна линейна, в
    будущем разных типов запросов может стать больше. Сюда же можно будет
    добавить дополнительную валидацию.

    Название переменной filter пересекается с названием функции python, в
    данном случае предпочитаю оставить так для сохранения аналогии с ES.

    Сортировка по одному полю, с указанием порядка (desc / asc).

    """

    bool_body_obj = BoolQueryBody(
        must=must and create_bool_rule(must, Must),
        must_not=must_not and create_bool_rule(must_not, MustNot),
        filter=filter and create_bool_rule(filter, Filter),
        should=should and create_bool_rule(should, Should),
        sort=sort and sort_factory(sort),
        page=size and page_factory(size, page or 1),

    )
    return bool_body_obj


def update_bool_query(bool_query, rule_name, obj_list):
    bool_query.update(
        {rule_name: [{'match': {obj.field: obj.value}} for obj in obj_list]}
    )


def create_bool_query(bool_obj) -> dict[str, Any]:
    """Нужно сформировать тело запроса из объекта BoolQueryBody.
    1) Сформировать bool запрос из объектов BoolQueryRule
    2) Сформировать значения "from" и "size" из объекта Page
    3) Сформировать значения "sort" из объекта Sort

    """
    bool_query = {}
    query_body = {"query": {"bool": bool_query}}

    if bool_obj.must:
        update_bool_query(bool_query, 'must', bool_obj.must)

    if bool_obj.must_not:
        update_bool_query(bool_query, 'must_not', bool_obj.must_not)

    if bool_obj.filter:
        update_bool_query(bool_query, 'filter', bool_obj.filter)

    if bool_obj.should:
        update_bool_query(bool_query, 'should', bool_obj.should)

    if bool_obj.sort:
        query_body["sort"] = {
            bool_obj.sort.field: {"order": bool_obj.sort.order}
        }

    if bool_obj.page:
        query_body["from"] = (bool_obj.page.number - 1) * bool_obj.page.size
        query_body["size"] = bool_obj.page.size

    return query_body


if __name__ == '__main__':
    import logging

    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    quary_obj = bool_simple_factory(
        must={'title': 'Star Wars'}, sort='-imdb_rating', size=10, page=1,
    )
    quary_body = create_bool_query(quary_obj)
    logger.info(create_curl_string(quary_body, 'movies'))