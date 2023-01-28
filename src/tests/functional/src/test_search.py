import uuid
import pytest


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'query': 'The Star'}, {'status': 200, 'length': 10}),
        ({'query': 'Mashed potato'}, {'status': 200, 'length': 0})
    ]
)
@pytest.mark.asyncio
async def test_search(make_get_request, es_write_data, query_data, expected_answer):
    # Генерируем данные для ES
    es_data = [{
        'id': str(uuid.uuid4()),
        'imdb_rating': 8.5,
        'genre': [
            {'id': str(uuid.uuid4()), 'name': 'Action'},
            {'id': str(uuid.uuid4()), 'name': 'Sci-Fi'}
        ],
        'title': 'The Star',
        'description': 'New World',
        'director': ['Stan'],
        'actors_names': ['Ann', 'Bob'],
        'writers_names': ['Ben', 'Howard'],
        'actors': [
            {'id': str(uuid.uuid4()), 'name': 'Ann'},
            {'id': str(uuid.uuid4()), 'name': 'Bob'}
        ],
        'writers': [
            {'id': str(uuid.uuid4()), 'name': 'Ben'},
            {'id': str(uuid.uuid4()), 'name': 'Howard'}
        ],
        'directors': [
            {'id': str(uuid.uuid4()), 'name': 'Jon'},
            {'id': str(uuid.uuid4()), 'name': 'Jane'}
        ]
    } for _ in range(60)]

    await es_write_data(data=es_data, index='movies', field_id='id')

    response = await make_get_request(url='/api/v1/films/search', params=query_data)

    # Проверяем ответ
    assert response.status == expected_answer['status']
    assert len(response.body['results']) == expected_answer['length']
