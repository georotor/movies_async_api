import pytest


@pytest.mark.parametrize(
    'url, params, answer',
    [
        (
            '/api/v1/films',
            {'page[size]': 10},
            {'status': 200, 'results': 10}
        ),
        (
            '/api/v1/films',
            {'page[size]': 50},
            {'status': 200, 'results': 50}
        ),
        (
            '/api/v1/films/search',
            {'query': 'lucas', 'page[size]': 10},
            {'status': 200, 'results': 10}
        ),
        (
            '/api/v1/films/search',
            {'query': 'lucas', 'page[size]': 50},
            {'status': 200, 'results': 50}
        ),
        (
            '/api/v1/persons',
            {'page[size]': 10},
            {'status': 200, 'results': 10}
        ),
        (
            '/api/v1/persons',
            {'page[size]': 50},
            {'status': 200, 'results': 50}
        ),
        (
            '/api/v1/persons/search',
            {'query': 'George', 'page[size]': 10},
            {'status': 200, 'results': 10}
        ),
        (
            '/api/v1/persons/search',
            {'query': 'George', 'page[size]': 50},
            {'status': 200, 'results': 25}
        ),
        (
            '/api/v1/genres',
            {'page[size]': 10},
            {'status': 200, 'results': 10}
        ),
        (
            '/api/v1/genres',
            {'page[size]': 20},
            {'status': 200, 'results': 20}
        ),
    ]
)
@pytest.mark.asyncio
async def test_page_size(make_get_request, es_write_data_all, url, params, answer):
    # Размер страницы
    response = await make_get_request(url=url, params=params)
    assert response.status == answer['status']
    assert len(response.body['results']) == answer['results']


@pytest.mark.parametrize(
    'url, params, answer',
    [
        (
                '/api/v1/films',
                {'page[number]': 1},
                {'status': 200, 'results': 10, 'id': 'e79b49dc-a5d9-46ec-a2c6-4cead985d732'}
        ),
        (
                '/api/v1/films',
                {'page[number]': 2},
                {'status': 200, 'results': 10, 'id': 'a0bdd4e7-84a0-4ec5-9dae-0d16371dc303'}
        ),
        (
                '/api/v1/films/search',
                {'query': 'lucas', 'page[number]': 1},
                {'status': 200, 'results': 10, 'id': 'cadefb3c-948c-4363-9f34-864cbc6d00d4'}
        ),
        (
                '/api/v1/films/search',
                {'query': 'lucas', 'page[number]': 2},
                {'status': 200, 'results': 10, 'id': '044beafe-fe25-4edc-95f4-adbb8979c35b'}
        ),
        (
                '/api/v1/persons',
                {'page[number]': 1},
                {'status': 200, 'results': 50, 'id': '2871f883-e001-4848-92d0-002adbdf2547'}
        ),
        (
                '/api/v1/persons',
                {'page[number]': 2},
                {'status': 200, 'results': 50, 'id': '26b6e17c-dc91-48f2-98d5-43c6c237ed1f'}
        ),
        (
                '/api/v1/genres',
                {'page[number]': 1},
                {'status': 200, 'results': 10, 'id': '3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff'}
        ),
        (
                '/api/v1/genres',
                {'page[number]': 2},
                {'status': 200, 'results': 10, 'id': 'fb58fd7f-7afd-447f-b833-e51e45e2a778'}
        ),
    ]
)
@pytest.mark.asyncio
async def test_page_number(make_get_request, es_write_data_all, url, params, answer):
    # Номер страницы
    response = await make_get_request(url=url, params=params)
    assert response.status == answer['status']
    assert len(response.body['results']) == answer['results']
    assert response.body['results'][0]['id'] == answer['id']


@pytest.mark.parametrize(
    'url, params, answer',
    [
        (
                '/api/v1/films',
                {
                    'page[size]': 10
                },
                {
                    'status': 200,
                    'results': 10
                }
        ),
        (
                '/api/v1/films/search',
                {
                    'query': 'lucas',
                    'page[size]': 10
                },
                {
                    'status': 200,
                    'results': 10
                }
        ),
        (
                '/api/v1/persons',
                {
                    'page[size]': 50
                },
                {
                    'status': 200,
                    'results': 50
                }
        ),
        (
                '/api/v1/persons/search',
                {
                    'query': 'George',
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
async def test_page_next(make_get_request, es_write_data_all, url, params, answer):
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
