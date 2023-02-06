import json
import pytest


@pytest.mark.parametrize(
    'url, cache_key, inject_field, inject_value',
    [
        (
            '/api/v1/films/search?query=lucas',
            "cache::services.film:search:(FilmService,):{'search': 'lucas', 'search_after': None, 'page_number': 1, 'size': 10}",
            'count',
            99999999999
        ),
        (
            '/api/v1/films/e79b49dc-a5d9-46ec-a2c6-4cead985d732',
            "cache::services.node:inner:('movies', UUID('e79b49dc-a5d9-46ec-a2c6-4cead985d732'), <class 'models.film.Film'>):{}",
            'title',
            'FROM_CACHE'
        ),
        (
            '/api/v1/films',
            "cache::services.film:get_films:(FilmService,):{'sort': None, 'search_after': None, 'filter_genre': None, 'size': 10, 'page_number': 1}",
            'count',
            99999999999
        ),
        (
            '/api/v1/persons/search?query=lucas',
            "cache::services.person:search:(PersonService,):{'search': 'lucas', 'size': 10, 'search_after': None, 'sort': 'name.raw'}",
            'count',
            99999999999
        ),
        (
            '/api/v1/persons/a5a8f573-3cee-4ccc-8a2b-91cb9f55250a/film',
            "cache::services.person:get_movies_with_person:(PersonService, UUID('a5a8f573-3cee-4ccc-8a2b-91cb9f55250a')):{}",
            'count',
            99999999999
        ),
        (
            '/api/v1/persons/a5a8f573-3cee-4ccc-8a2b-91cb9f55250a',
            "cache::services.node:inner:('persons', UUID('a5a8f573-3cee-4ccc-8a2b-91cb9f55250a'), <class 'models.person.PersonDetails'>):{}",
            'name',
            'FROM_CACHE'
        ),
        (
            '/api/v1/persons',
            "cache::services.person:get_persons:(PersonService,):{'size': 50, 'search_after': None}",
            'count',
            99999999999
        ),
        (
            '/api/v1/genres/3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff',
            "cache::services.node:inner:('genres', UUID('3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff'), <class 'models.genre.Genre'>):{}",
            'name',
            'FROM_CACHE'
        ),
        (
            '/api/v1/genres',
            "cache::services.genre:get_genres:(GenreService,):{'size': 10, 'page_number': 1}",
            'count',
            99999999999
        ),
    ]
)
@pytest.mark.asyncio
async def test_redis(redis_client, make_get_request, es_write_data_all, url, cache_key, inject_field, inject_value):
    """
    План тестирования:
    - удаляем кэш по ключу и запрашиваем API, убеждаемся что данные попадают в кэш
    - делаем инъекцию в кэш и запрашиваем данные через API, убеждаемся что данные отдаются из кэша
    """
    await redis_client.delete(cache_key)
    await make_get_request(url)
    cache_data = await redis_client.get(cache_key)
    assert cache_data

    cache_data = json.loads(cache_data)
    cache_data[inject_field] = inject_value
    await redis_client.set(cache_key, json.dumps(cache_data))
    response = await make_get_request(url)
    await redis_client.delete(cache_key)
    assert response.body[inject_field] == inject_value
