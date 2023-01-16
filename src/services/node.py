from functools import wraps
from typing import Optional, Callable
from uuid import UUID

import orjson
from elasticsearch import AsyncElasticsearch, NotFoundError
from pydantic import BaseModel

from src.services.cache_managers.abstract_manager import AbstractManager

NODE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


def cache_support(func: Callable):
    """Декоратор, добавляет поддержку кэширования в Redis.
    1) считает ключ по хэшу (args, kwargs)
    2) если его находит в кэше - отдает
    3) если нет - выполняет первоночальную функцию и кэширует результат

    Args:
        func - декорируемая функция для поиска данных в БД.
    Returns:
        BaseModel либо список из BaseModel, в зависимости от типа запроса.

    """
    @wraps(func)
    async def inner(self, *args, **kwargs):
        cache_id = self.redis_manager.create_id((args, kwargs))
        cache_value = await self.redis_manager.get(cache_id)

        if cache_value:
            decode_value = orjson.loads(cache_value)
            if isinstance(decode_value, list):
                return [self.model.parse_raw(x) for x in decode_value]
            return self.model.parse_raw(decode_value)

        else:
            fresh_value = await func(self, *args, **kwargs)
            await self.redis_manager.put(
                cache_id, orjson.dumps(fresh_value, default=self.model.json)
            )
            return fresh_value
    return inner


class NodeService:
    """Сервис по получению данных из ES. Поддерживает кэширование в Redis. """
    def __init__(
            self,
            redis_manager: AbstractManager,
            elastic: AsyncElasticsearch,
            model,
            es_index: str
    ):
        """Конструктор класса.

        Args:
          redis_manager: инициализированный менеджер для работы с Redis;
          elastic: инициализированное подключение к БД;
          model: модель pydantic описывающая объект;
          es_index: название индекса ES;

        """
        self.redis_manager = redis_manager
        self.elastic = elastic
        self.model = model
        self.es_index = es_index

    @cache_support
    async def get_by_id(self, node_id: UUID) -> BaseModel | None:
        """Получение одного объекта по id. Декоратор добавляет поддержку кэша.

        Args:
          node_id: id объекта в ES.
        Returns:
            BaseModel

        """
        node = await self._get_from_elastic(node_id)
        return node

    async def _get_from_elastic(self, node_id: UUID) -> BaseModel | None:
        """Выполняет get запрос в ES. Если данные там есть - возвращаем в виде
        объекта pydantic.

        Args:
          node_id: id объекта в ES;
        Returns:
            BaseModel

        """
        try:
            doc = await self.elastic.get(self.es_index, node_id)
        except NotFoundError:
            return None
        return self.model(**doc['_source'])

    @cache_support
    async def search(
            self,
            search_string: Optional[str],
            sort: Optional[list] = None,
            page_number=1,
            size=10
    ) -> list[BaseModel] | None:
        """Поиск подходящих объектов по ключевому слову. Декоратор добавляет
        поддержку кэша.

        Args:
          search_string: поисковый запрос;
          sort: список с ключами сортировки;
          page_number: номер текущей страницы;
          size: кол-во объектов на странице;
        Returns:
            Данные представлены в виде списка BaseModel.

        """
        nodes_list = await self._search_in_elastic(
            search_string, sort, size, page_number,
        )

        return nodes_list

    async def _search_in_elastic(
            self,
            search_string: Optional[str] = None,
            sort: Optional[list] = None,
            page_number=1,
            size=10
    ) -> list | None:
        """Выполняет match_all запрос в ES. В будущем желательно вынести работу
        с ES в отдельный модуль.

        Args:
          search_string: поисковый запрос;
          sort: список с ключами сортировки;
          page_number: номер текущей страницы;
          size: кол-во объектов на странице;
        Returns:
            Данные представлены в виде списка BaseModel.

        """

        body = {
            "from": (page_number - 1) * size,
            "size": size,
            "query": {"match_all": {}}
        }

        if search_string:
            body["query"] = {"query_string": {"query": search_string}}

        if sort:
            body["sort"] = sort

        try:
            docs = await self.elastic.search(index=self.es_index, body=body)
        except NotFoundError:
            return None

        return [self.model(**_doc["_source"]) for _doc in docs["hits"]["hits"]]
