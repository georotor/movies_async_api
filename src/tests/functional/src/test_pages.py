import pytest


@pytest.mark.parametrize(
    'url, params, answer',
    [
        (
            '/films',
            {'page[size]': 10},
            {'status': 200, 'results': 10}
        ),
        (
            '/films',
            {'page[size]': 50},
            {'status': 200, 'results': 50}
        ),
        (
            '/films/search',
            {'query': 'lucas', 'page[size]': 10},
            {'status': 200, 'results': 10}
        ),
        (
            '/films/search',
            {'query': 'lucas', 'page[size]': 50},
            {'status': 200, 'results': 50}
        )
    ]
)
@pytest.mark.asyncio
async def test_page_size(make_get_request, es_write_data_movies, url, params, answer):
    # Размер страницы
    response = await make_get_request(url=url, params=params)
    assert response.status == answer['status']
    assert len(response.body['results']) == answer['results']


@pytest.mark.parametrize(
    'url, params, answer',
    [
        (
            '/films',
            {'page[number]': 1},
            {'status': 200, 'results': 10, 'id': 'e79b49dc-a5d9-46ec-a2c6-4cead985d732'}
        ),
        (
            '/films',
            {'page[number]': 2},
            {'status': 200, 'results': 10, 'id': 'a0bdd4e7-84a0-4ec5-9dae-0d16371dc303'}
        ),
        (
            '/films/search',
            {'query': 'lucas', 'page[number]': 1},
            {'status': 200, 'results': 10, 'id': 'cadefb3c-948c-4363-9f34-864cbc6d00d4'}
        ),
        (
            '/films/search',
            {'query': 'lucas','page[number]': 2},
            {'status': 200, 'results': 10, 'id': '044beafe-fe25-4edc-95f4-adbb8979c35b'}
        )
    ]
)
@pytest.mark.asyncio
async def test_page_number(make_get_request, es_write_data_movies, url, params, answer):
    # Номер страницы
    response = await make_get_request(url=url, params=params)
    assert response.status == answer['status']
    assert len(response.body['results']) == answer['results']
    assert response.body['results'][0]['id'] == answer['id']


@pytest.mark.parametrize(
    'url, params, answer',
    [
        (
            '/films',
            {
                'page[size]': 10
            },
            {
                'status': 200,
                'results': 10
            }
        ),
        (
            '/films/search',
            {
                'query': 'lucas',
                'page[size]': 10
            },
            {
                'status': 200,
                'results': 10
            }
        )
    ]
)
@pytest.mark.asyncio
async def test_page_next(make_get_request, es_write_data_movies, url, params, answer):
    # Следующая страница
    response = await make_get_request(url=url, params=params)
    assert response.status == answer['status']
    assert len(response.body['results']) == answer['results']
    assert response.body['next']
    # Пробуем запросить следующую страницу
    next_response = await make_get_request(url=url, params={**params, 'page[next]': response.body['next']})
    assert next_response.status == 200
    assert len(next_response.body['results']) > 0
    assert response.body['results'][0]['id'] != next_response.body['results'][0]['id']
