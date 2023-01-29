import asyncio
import json
from dataclasses import dataclass
from typing import List

import aiohttp
import pytest
from elasticsearch import AsyncElasticsearch
from multidict import CIMultiDictProxy

from tests.functional.settings import test_settings


def get_es_bulk_query(data: list[dict], es_index: str, es_id_field: str) -> list[str]:
    """
    Подготовка списка с данными для bulk запроса в Elasticsearch.

    :param data: Данные для bulk запроса.
    :param es_index: Индекс, в который будут вставляться данные.
    :param es_id_field: Название поля из data, которое будет использовано в качестве id.
    :return: Список для bulk запроса.
    """
    bulk_query = []
    for row in data:
        bulk_query.extend([
            json.dumps({'index': {'_index': es_index, '_id': row[es_id_field]}}),
            json.dumps(row)
        ])
    return bulk_query


async def get_data_from_file(fl: str) -> list[dict]:
    """
    Считывание предварительно подготовленных данных из файла.
    Можно сделать асинхронно через aiofiles, но зачем?

    :param fl: Название файла.
    :return: Список подготовленных данных.
    """
    with open(f'tests/functional/testdata/{fl}', 'r', encoding='UTF-8') as file:
        data = [json.loads(line) for line in file]
    return data


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


@pytest.fixture(scope='session')
async def session():
    """ Единая сессия для всех тестов. """
    client_session = aiohttp.ClientSession()
    yield client_session
    await client_session.close()


@pytest.fixture
def make_get_request(session):
    """
    Фикстура для выполнения GET запросов.

    :param session: Клиент aiohttp.
    :return: Функция выполнения GET запросов.
    """
    async def inner(url: str, params: dict | None = None):
        """
        Фикстура для выполнения GET запросов к API
        :param url: URL запроса.
        :param params: Словарь с параметрами для запроса.
        :return: Ответ в виде HTTPResponse объекта.
        """
        params = params or {}
        url = test_settings.service_url + test_settings.api_url + url
        async with session.get(url, params=params) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )
    return inner


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def es_client():
    """ Клиент для Elasticsearch. """
    client = AsyncElasticsearch(hosts=test_settings.elastic_host, validate_cert=False, use_ssl=False)
    yield client
    await client.close()


@pytest.fixture(scope='session')
def es_write_data(es_client: AsyncElasticsearch):
    """
    Фикстура для записи данных в Elasticsearch.

    :param es_client: Клиент для Elasticsearch.
    :return: Функция вставки данных через bulk запрос.
    """
    async def inner(data: list[dict], index: str, field_id: str):
        bulk_query = get_es_bulk_query(data, index, field_id)
        str_query = '\n'.join(bulk_query) + '\n'

        response = await es_client.bulk(body=str_query, refresh=True)

        if response['errors']:
            raise Exception('Ошибка записи данных в Elasticsearch')
    return inner


@pytest.fixture(scope='session')
async def es_write_data_movies(es_write_data):
    """
    Фикстура заполнения индекса movies в Elasticsearch.

    :param es_write_data: Функция записи данных в Elasticsearch.
    """
    data = await get_data_from_file('movies.json')
    await es_write_data(data=data, index='movies', field_id='id')


@pytest.fixture(scope='session')
async def es_write_data_persons(es_write_data):
    """
    Фикстура заполнения индекса persons в Elasticsearch.

    :param es_write_data: Функция записи данных в Elasticsearch.
    """
    data = await get_data_from_file('persons.json')
    await es_write_data(data=data, index='persons', field_id='id')


@pytest.fixture(scope='session')
async def es_write_data_genres(es_write_data):
    """
    Фикстура заполнения индекса genres в Elasticsearch.

    :param es_write_data: Функция записи данных в Elasticsearch.
    """
    data = await get_data_from_file('genres.json')
    await es_write_data(data=data, index='genres', field_id='id')
