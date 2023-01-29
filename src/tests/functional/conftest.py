import asyncio
import json
from dataclasses import dataclass
from multidict import CIMultiDictProxy

import aiohttp
import pytest
from elasticsearch import AsyncElasticsearch

from tests.functional.settings import test_settings


def get_es_bulk_query(data, es_index, es_id_field):
    bulk_query = []
    for row in data:
        bulk_query.extend([
            json.dumps({'index': {'_index': es_index, '_id': row[es_id_field]}}),
            json.dumps(row)
        ])
    return bulk_query


async def get_data_from_file(fl: str) -> list[dict]:
    # Можно сделать асинхронно через aiofiles, но зачем?
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
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture
def make_get_request(session):
    async def inner(url: str, params: dict | None = None):
        params = params or {}
        url = test_settings.service_url + url
        async with session.get(url, params=params) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )
    return inner


@pytest.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(hosts=test_settings.elastic_host, validate_cert=False, use_ssl=False)
    yield client
    await client.close()


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def es_write_data(es_client: AsyncElasticsearch):
    async def inner(data: list[dict], index: str, field_id: str):
        bulk_query = get_es_bulk_query(data, index, field_id)
        str_query = '\n'.join(bulk_query) + '\n'

        response = await es_client.bulk(body=str_query, refresh=True)

        if response['errors']:
            raise Exception('Ошибка записи данных в Elasticsearch')
    return inner


@pytest.fixture(scope='session')
async def es_write_data_movies(es_write_data):
    data = await get_data_from_file('movies.json')
    await es_write_data(data=data, index='movies', field_id='id')


@pytest.fixture(scope='session')
async def es_write_data_persons(es_write_data):
    data = await get_data_from_file('persons.json')
    await es_write_data(data=data, index='persons', field_id='id')


@pytest.fixture(scope='session')
async def es_write_data_genres(es_write_data):
    data = await get_data_from_file('genres.json')
    await es_write_data(data=data, index='genres', field_id='id')
