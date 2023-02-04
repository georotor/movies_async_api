from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from pydantic import BaseModel


class DBManagerError(Exception):
    """Исключение, вызывается при ошибках в работе AbstractDBManager."""


class AbstractDBManager(ABC):
    """Описание интерфейса для поиска данных в БД. Возвращает данные в виде
    объектов pydantic. Это позволяет:
        1) решить проблему с валидацией найденных данных;
        2) унифицировать выходные данные (не зависеть от типа и версии БД).

    В первую очередь рассчитан на работу с Elastic, но при желании несложно
    написать реализацию и для других БД.

    """

    @abstractmethod
    async def get(
            self, table_name: str, object_id: Any, model: Type[BaseModel]
    ) -> Optional[BaseModel]:
        """Поиск объекта в указанный таблице (индексе). Метод должен возвращать
        один единственный объект.

        Args:
          table_name: название таблицы (индекса);
          object_id: уникальный идентификатор, тип данных стоит указать в
          конкретных реализациях;
          model: модель pydantic со списком нужных полей.

        Returns:
            Экземпляр pydantic BaseModel с данными из БД.

        """

    @abstractmethod
    async def search_all(
            self,
            table_name: str,
            model: Type[BaseModel],
            query: Any,
    ) -> tuple[list[Optional[BaseModel]], int, list]:
        """Поиск по всем полям указанной таблицы (индекса). Возвращает список
        объектов и значение search_after.

        Args:
          table_name: название таблицы (индекса);
          model: модель pydantic со списком нужных полей;
          query: сформированное тело запроса;

        Returns:
            Кортеж из трех значений:
              - список моделей pydantic BaseModel с данными из БД;
              - общее количество найденных записей (без учета пагинации);
              - значение search_after (стартовое значение для следующей выдачи,
                термин из Elastic, при желании можно реализовать и для SQL).

        """
