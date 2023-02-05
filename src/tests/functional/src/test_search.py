import pytest


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'query': 'The Star'}, {'status': 200, 'length': 10}),
        ({'query': 'NotFound'}, {'status': 200, 'length': 0})
    ]
)
@pytest.mark.asyncio
async def test_search(make_get_request, es_write_data_movies, query_data, expected_answer):

    response = await make_get_request(url='/api/v1/films/search', params=query_data)

    # Проверяем ответ
    assert response.status == expected_answer['status']
    assert len(response.body['results']) == expected_answer['length']
