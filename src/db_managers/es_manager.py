from typing import Optional, Type
from uuid import UUID

from elasticsearch import (AsyncElasticsearch, ElasticsearchException,
                           NotFoundError)
from pydantic import BaseModel

from db_managers.abstract_manager import AbstractDBManager, DBManagerError


class ESDBManager(AbstractDBManager):
    def __init__(self, elastic: AsyncElasticsearch):
        """Реализация AbstractDBManager для работы с Elastic. Перехватывает
        корневое исключение ElasticsearchException и меняет на DBManagerError.

        Args:
          elastic: инициализированное подключение к БД;

        """
        self.elastic = elastic

    async def get(
            self, table_name: str, object_id: UUID, model: Type[BaseModel]
    ) -> Optional[BaseModel]:
        """Поиск объекта в указанном индексе. Метод должен возвращать
        один единственный объект.

        Args:
          table_name: название индекса;
          object_id: уникальный идентификатор, в данном случае UUID;
          model: модель pydantic со списком нужных полей.

        Returns:
            Экземпляр pydantic BaseModel с данными из БД.

        """
        try:
            # Приводим id к строке ради корректной подсветки синтаксиса
            doc = await self.elastic.get(index=table_name, id=str(object_id))
            return model(**doc['_source'])
        except NotFoundError:
            return None
        except ElasticsearchException as e:
            raise DBManagerError('ElasticsearchException: {}'.format(e))

    async def search_all(
            self,
            table_name: str,
            model: Type[BaseModel],
            query: dict
    ) -> tuple[list[Optional[BaseModel]], int, list]:
        """Реализация абстрактного метода. Поиск по всем полям указанного
        индекса. Возвращает список объектов и значение search_after.

        Про последнее можно почитать вот тут:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/paginate-search-results.html
        https://stackoverflow.com/questions/68127892/how-does-search-after-work-in-elastic-search

        Args:
          table_name: название индекса;
          model: модель pydantic со списком нужных полей;
          query: сформированное тело запроса.

        Returns:
            Кортеж из трех значений:
              - список моделей pydantic BaseModel с данными из БД;
              - общее количество найденных записей (без учета пагинации);
              - значение search_after (стартовое значение для следующей выдачи,
                термин из Elastic, при желании можно реализовать и для SQL).

        """
        try:
            docs = await self.elastic.search(index=table_name, body=query)
            hits = docs['hits']['hits']
            if hits:
                models = [model.parse_obj(doc['_source']) for doc in hits]
                search_after = docs['hits']['hits'][-1].get("sort", [])
                total = docs['hits']['total']['value']
                return models, total, search_after
            return [], 0, []

        except NotFoundError:
            return [], 0, []
        except ElasticsearchException as e:
            raise DBManagerError('ElasticsearchException: {}'.format(e))
