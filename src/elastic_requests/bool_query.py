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
        self._body = {'query': {'bool': {boolean_clause: []}}}
        self.boolean_clause = boolean_clause

    def add_search_condition(
            self, search: str, field_name: Optional[str] = None
    ):
        """Простое условие на основе query_string. С параметрами по умолчанию
        релевантность поиска оставляет желать лучшего. Нужно или указывать
        default_field (тогда поиск будет вестись только по нему) или задать
        коэффициенты полей (boosting) в списке "fields". Второй вариант мне
        нравится больше - он позволяет добиться релевантных результатов не
        ограничивая поиск одним единственным полем.

        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        query-dsl-query-string-query.html#query-string-top-level-params

        Для нечеткого (fuzzy) поиска, в конце строки search нужно добавить "~".
        В документации советуют установить значение fuzziness на auto, но это
        позволяет обойти только простые опечатки. "George~ LucaZ~" - находит,
        а "George~ LucOs~" - уже нет. Это можно решить, выставив fuzziness = 2,
        но так заметно падает релевантность при поиске фильмов.

        Args:
          search: строка с данными для поиска;
          field_name: основное поле для поиска, получит значение boosting ^5;

        """
        rule = {'query_string': {'query': search, 'default_operator': 'and'}}
        rule['query_string']['fuzziness'] = 'auto'
        if field_name:
            rule['query_string']['fields'] = ['{}^5'.format(field_name), '*']

        self._body['query']['bool'][self.boolean_clause].append(rule)

    def insert_nested_query(self, search: Any, obj_name: str, obj_field: str):
        """Простое условие для поиска по вложенным (nested) объектам.

        https://www.elastic.co/guide/en/elasticsearch/reference/7.17/
        query-dsl-nested-query.html#query-dsl-nested-query

        Args:
          search: строка с данными для поиска;
          obj_name: название вложенного (nested) объекта;
          obj_field: поле вложенного (nested) объекта;

        """
        nested_rule = {'{}.{}'.format(obj_name, obj_field): search}
        rule = {'nested': {'query': {'term': nested_rule}, 'path': obj_name}}

        self._body['query']['bool'][self.boolean_clause].append(rule)


def sort_factory(sort: str, default_sort: Optional[dict] = None) -> list[dict]:
    """Фабрика для создания сортировки. Учитывая повсеместное использование
    search_after, сортировка требует отдельного внимания. Нужно убедиться, что
    в условиях присутствует хотя бы одно уникальной поле. В нашем случае id.

    Args:
      sort: строка с указанием поля сортировки в стиле Django: минус в начале
        строки указывает на обратный порядок сортировки, пр. '-imdb_rating',
        допустимо перечисление полей через ',';
      default_sort: правило сортировки с уникальным полем.

    """
    default_sort = default_sort or {'id': {'order': 'asc'}}
    _sort = []
    if sort:
        for item in sort.split(','):
            _sort.append({item.lstrip('-'): 'desc' if item.startswith('-') else 'asc'})
        # TODO: проверить этот блок на правильную логику
        if "id" not in sort.split(','):
            _sort.append(default_sort)
    else:
        _sort = default_sort

    return _sort


def must_query_factory(
    search: Optional[str] = None,
    default_field: Optional[str] = None,
    search_after: Optional[list] = None,
    sort: str = 'id',
    size: Optional[int] = None,
    page_number: Optional[int] = None,
    related_search: Optional[dict[str, str | UUID]] = None,
):
    """Фабрика для создания и инициализации объекта BoolQuery с логической
    группой "must". Каждый раз при формировании запроса в Elastic требуется
    выполнять однотипные действия - формировать параметры сортировки, добавлять
    пагинацию, search_after и т.д. Имеет смысл вынести код в отдельную функцию,
    а не дублировать по нескольку раз для каждого сервиса.

    Так как практически везде используется параметр search_after, в запросе
    обязательно должна быть сортировка по уникальному полю - в нашем случае id.

    Args:
      search: строка с данными для поиска;
      default_field: строка с названием приоритетного поля для поиска;
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
        search = ' '.join(['{}'.format(x) for x in search.split()])
        query.add_search_condition(search, default_field)

    sort_ = sort_factory(sort)
    query.add_sort(sort_, search_after)

    if related_search:
        for search_path, search_string in related_search.items():
            obj, field = search_path.split('.')
            query.insert_nested_query(search_string, obj, field)
    return query
