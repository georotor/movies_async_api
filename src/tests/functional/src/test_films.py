import pytest
from http import HTTPStatus


pytestmark = pytest.mark.asyncio


async def test_film(make_get_request, es_write_data_movies):
    # Проверяем фильм
    film_id = 'cadefb3c-948c-4363-9f34-864cbc6d00d4'
    response = await make_get_request(url=f'/api/v1/films/{film_id}')
    assert response.status == HTTPStatus.OK
    assert response.body['id'] == film_id
    assert response.body['title'] == 'Saving Star Wars'


async def test_film_notfound(make_get_request, es_write_data_movies):
    # Отсутствие фильма
    film_id = 'cadefb3c-948c-4363-9f34-864cbc6d00d0'
    response = await make_get_request(url=f'/api/v1/films/{film_id}')
    assert response.status == HTTPStatus.NOT_FOUND


async def test_film_valid_id(make_get_request, es_write_data_movies):
    # Валидацию id
    film_id = '000'
    response = await make_get_request(url=f'/api/v1/films/{film_id}')
    assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_films(make_get_request, es_write_data_movies):
    # Список фильмов
    response = await make_get_request(url=f'/api/v1/films')
    assert response.status == HTTPStatus.OK
    assert response.body['count'] == 999
    assert response.body[
               'next'] == 'WyIyMDAxIE1MQiBBbGwtU3RhciBHYW1lIiwiNjY3ZGJlOTAtNDY0OC00N2ZjLTgzYTktY2E3YzcxMzkyYTRlIl0'
    assert len(response.body['results']) == 10
    assert response.body['results'][0]['id'] == 'e79b49dc-a5d9-46ec-a2c6-4cead985d732'


@pytest.mark.parametrize(
    'params, answer',
    [
        ({'sort': 'imdb_rating'}, {'status': HTTPStatus.OK, 'id': 'e7e6d147-cc10-406c-a7a2-5e0be2231327'}),
        ({'sort': '-imdb_rating'}, {'status': HTTPStatus.OK, 'id': '2a090dde-f688-46fe-a9f4-b781a985275e'})
    ]
)
async def test_films_sort(make_get_request, es_write_data_movies, params, answer):
    # Сортировка фильмов
    response = await make_get_request(url=f'/api/v1/films', params=params)
    assert response.status == answer['status']
    assert response.body['results'][0]['id'] == answer['id']


@pytest.mark.parametrize(
    'params, answer',
    [
        ({'filter[genre]': '3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff'},
         {'status': HTTPStatus.OK,
          'count': 244,
          'next': 'WyJDb25mZXNzaW9ucyBvZiBhbiBBY3Rpb24gU3RhciIsImNlNmU0MWEyLWFjMzgtNDQzYS1iNGVjLTEwMzA3YjRlMGIzOCJd',
          'results': 10}),
        ({'filter[genre]': '3d8d9bf5-0d90-4353-88ba-4ccc5d2c0700'},
         {'status': HTTPStatus.OK,
          'count': 0,
          'next': None,
          'results': 0})
    ]
)
async def test_films_filter(make_get_request, es_write_data_movies, params, answer):
    # Фильтр фильмов
    response = await make_get_request(url=f'/api/v1/films', params=params)
    assert response.status == answer['status']
    assert response.body['count'] == answer['count']
    assert response.body['next'] == answer['next']
    assert len(response.body['results']) == answer['results']


@pytest.mark.parametrize(
    'params, answer',
    [
        ({'query': 'superman'},
         {'status': HTTPStatus.OK,
          'count': 1,
          'results': 1,
          'id': '9c7dc26a-489d-4c08-9bba-6ae9dc8117f1'
          }),
        ({'query': 'lucas'},
         {'status': HTTPStatus.OK,
          'count': 54,
          'results': 10,
          'id': 'cadefb3c-948c-4363-9f34-864cbc6d00d4'}),
        ({'query': 'alise'},
         {'status': HTTPStatus.OK,
          'count': 0,
          'results': 0})
    ]
)
async def test_films_sort(make_get_request, es_write_data_movies, params, answer):
    # Поиск фильмов
    response = await make_get_request(url=f'/api/v1/films/search', params=params)
    assert response.status == answer['status']
    assert response.body['count'] == answer['count']
    assert len(response.body['results']) == answer['results']
    if 'id' in answer:
        assert response.body['results'][0]['id'] == answer['id']
