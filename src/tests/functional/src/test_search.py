import datetime
import uuid
import json

import aiohttp
import pytest

from elasticsearch import AsyncElasticsearch

from tests.functional.settings import test_settings


@pytest.mark.asyncio
async def test_search():
    # 1. Генерируем данные для ES

    es_data = [{
        'id': str(uuid.uuid4()),
        'imdb_rating': 8.5,
        'genre': [
            {'id':  str(uuid.uuid4()), 'name': 'Action'},
            {'id':  str(uuid.uuid4()), 'name': 'Sci-Fi'}
        ],
        'title': 'The Star',
        'description': 'New World',
        'director': ['Stan'],
        'actors_names': ['Ann', 'Bob'],
        'writers_names': ['Ben', 'Howard'],
        'actors': [
            {'id':  str(uuid.uuid4()), 'name': 'Ann'},
            {'id':  str(uuid.uuid4()), 'name': 'Bob'}
        ],
        'writers': [
            {'id':  str(uuid.uuid4()), 'name': 'Ben'},
            {'id':  str(uuid.uuid4()), 'name': 'Howard'}
        ],
        'directors': [
            {'id':  str(uuid.uuid4()), 'name': 'Jon'},
            {'id':  str(uuid.uuid4()), 'name': 'Jane'}
        ]
    } for _ in range(60)]

    bulk_query = []
    for row in es_data:
        bulk_query.extend([
            json.dumps({'index': {'_index': test_settings.es_index, '_id': row[test_settings.es_id_field]}}),
            json.dumps(row)
        ])

    str_query = '\n'.join(bulk_query) + '\n'

    # 2. Загружаем данные в ES

    es_client = AsyncElasticsearch(hosts=test_settings.elastic_host,
                                   validate_cert=False,
                                   use_ssl=False)
    response = await es_client.bulk(str_query, refresh=True)
    await es_client.close()
    if response['errors']:
        raise Exception('Ошибка записи данных в Elasticsearch')

    # 3. Запрашиваем данные из ES по API

    session = aiohttp.ClientSession()
    url = test_settings.service_url + '/api/v1/films/search'
    query_data = {'query': 'The Star'}
    async with session.get(url, params=query_data) as response:
        body = await response.json()
        headers = response.headers
        status = response.status
    await session.close()

    # 4. Проверяем ответ
    assert status == 200
    assert len(body['results']) == 10
