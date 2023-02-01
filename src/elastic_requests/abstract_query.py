"""В Elastic много видов поисковых запросов для четкого и нечеткого поиска.
И у каждого есть ряд параметров и особенностей. С развитием API типов запросов
потребуется больше. Например, если потребуется одновременно искать фильмы по
жанру и имени актера, "must" придется менять на "should". Хочется иметь
возможность делать это "на лету", с сохранением старого интерфейса.

По этой причине вся генерация запросов отвязана от классов для работы с БД или
сервисами API и вынесена в отдельный модуль.

"""

from abc import ABC, abstractmethod
from typing import Any, Literal, Optional


class AbstractQuery(ABC):
    _body = {'query': {'match_all': {}}}

    @property
    def body(self):
        self._validate_body()
        return self._body

    def _validate_body(self):
        """При использовании search_after дополнительное смещение не нужно."""
        if 'search_after' in self._body and 'from' in self._body:
            del self._body['from']

    def add_pagination(self, page_number=1, size=10):
        self._body['size'] = size
        self._body['from'] = (page_number - 1) * size

    def add_sort(
            self,
            sort: list[dict[str, Literal['asc', 'desc']]],
            search_after: Optional[list] = None,
    ):
        """Добавление сортировки и параметра search_after (стартового значения
        для следующей выдачи).

        """
        self._body['sort'] = sort
        if search_after:
            self._body['search_after'] = search_after

    @abstractmethod
    def add_search_condition(
            self, search: str, field_name: Optional[str] = None
    ):
        """Добавление нового условия поиска по полям объекта."""

    @abstractmethod
    def insert_nested_query(self, search: Any, obj_name: str, obj_field: str):
        """Добавление условия для поиска по вложенным (nested) объектам."""
