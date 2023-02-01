"""Модуль для работы с запросами типа Bool. Структура запроса:

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

from typing import Any, Literal, Optional
from uuid import UUID

from elastic_requests.abstract_query import AbstractQuery


class BoolQuery(AbstractQuery):
    """Генератор простого bool запроса с поддержкой нескольких условий.
    По умолчанию оставляем список правил boolean_clause пустым, при желании
    можно изменить на {"match_all": {}}, я не заметил разницы.

    """

    def __init__(self, boolean_clause: Literal['must', 'should'] = "must"):
        """Bool позволяют разбивать условия поиска сразу по нескольким
        логическим группам. Нам пока достаточно одной группы за раз - это либо
        "must" (обязательное соответствие), либо "should" (соответствие хотя бы
        одному из перечисленных условий, логическое "OR").

        Args:
          boolean_clause: тип группы запросов;

        """
        self.body = {"query": {"bool": {boolean_clause: []}}}
        self.boolean_clause = boolean_clause

    def add_search_condition(
            self, search: str, field_name: Optional[str] = None
    ):
        """Простое условие на основе query_string. В будущем можно будет
        добавить разные коэффициенты для разных полей (boosting).

        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        query-dsl-query-string-query.html#query-string-top-level-params

        Args:
          search: строка с данными для поиска;
          field_name: дефолтное поле для поиска, поддерживает маски (*);

        """
        rule = {"query_string": {"query": search}}
        if field_name:
            rule['default_field'] = field_name

        self.body["query"]["bool"][self.boolean_clause].append(rule)

    def insert_nested_query(self, search: Any, obj_name: str, obj_field: str):
        """Простое условие для поиска по вложенным (nested) объектам.

        https://www.elastic.co/guide/en/elasticsearch/reference/7.17/
        query-dsl-nested-query.html#query-dsl-nested-query

        Args:
          search: строка с данными для поиска;
          obj_name: название вложенного (nested) объекта;
          obj_field: поле вложенного (nested) объекта;

        """
        nested_rule = {"{}.{}".format(obj_name, obj_field): search}
        rule = {"nested": {"query": {"term": nested_rule}, "path": "genre"}}

        self.body["query"]["bool"][self.boolean_clause].append(rule)


def must_query_factory(
    search: Optional[str] = None,
    search_after: Optional[list] = None,
    sort: Optional[str] = None,
    size: Optional[int] = None,
    page_number: Optional[int] = None,
    related_search: Optional[dict[str, str | UUID]] = None,
):
    """Фабрика для создания и инициализации объекта BoolQuery с логической
    группой "must". Каждый раз при формировании запроса в Elastic требуется
    выполнять однотипные действия - формировать параметры сортировки, добавлять
    пагинацию, search_after и т.д. Имеет смысл вынести код в отдельную функцию,
    а не дублировать по нескольку раз для каждого сервиса.

    Args:
      search: строка с данными для поиска;
      search_after: стартовое значение для следующей выдачи, не работает
        без sort;
      sort: строка с указанием поля сортировки в стиле Django: минус в начале
        строки указывает на обратный порядок сортировки, пр. '-imdb_rating';
      size: кол-во записей на странице (limit);
      page_number: номер страницы;
      related_search: поиск во вложенных (nested) объектах. Ключ - поле для
        поиска в формате 'nested_object.field', значение - поисковой запрос.
        Пр. {'genre.id': '526769d7-df18-4661-9aa6-49ed24e9dfd8'}

    Returns:
        Список моделей pydantic BaseModel с данными из БД и значение
        search_after для следующего поиска.

    """
    query = BoolQuery()
    if page_number and size:
        query.add_pagination(page_number, size)
    if search:
        query.add_search_condition(search)
    if sort:
        sort_ = [{sort.lstrip('-'): 'desc' if sort.startswith('-') else 'asc'}]
        query.add_sort(sort_, search_after)

    if related_search:
        for search_path, search_string in related_search.items():
            obj, field = search_path.split('.')
            query.insert_nested_query(search_string, obj, field)

    return query
