import pytest


@pytest.mark.asyncio
async def test_genre(make_get_request, es_write_data_genres):
    # Проверяем genre
    genre_id = "120a21cf-9097-479e-904a-13dd7198c1dd"
    response = await make_get_request(url=f"/api/v1/genres/{genre_id}")
    assert response.status == 200
    assert response.body["id"] == genre_id
    assert response.body["name"] == "Adventure"


@pytest.mark.asyncio
async def test_genre_notfound(make_get_request, es_write_data_genres):
    # Отсутствие genre
    genre_id = "cadefb3c-948c-4363-9f34-864cbc6d00d0"
    response = await make_get_request(url=f"/api/v1/genres/{genre_id}")
    assert response.status == 404


@pytest.mark.asyncio
async def test_genre_valid_id(make_get_request, es_write_data_genres):
    # Валидацию genre_id
    genre_id = "20a21cf-997-49e-94a-13d7198c1dd"
    response = await make_get_request(url=f"/api/v1/genres/{genre_id}")
    assert response.status == 422


@pytest.mark.asyncio
async def test_genres(make_get_request, es_write_data_genres):
    # Список genres
    response = await make_get_request(url=f"/api/v1/genres")
    assert response.status == 200
    assert response.body["count"] == 26
    assert len(response.body["results"]) == 10
    assert response.body["results"][0]["id"] == "3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff"


@pytest.mark.asyncio
async def test_genres_page_size(make_get_request, es_write_data_genres):
    # Список genres
    response = await make_get_request(url=f"/api/v1/genres?page[size]=20")
    assert response.status == 200
    assert response.body["count"] == 26
    assert len(response.body["results"]) == 20
    assert response.body["results"][0]["id"] == "3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff"


@pytest.mark.asyncio
async def test_genres_page_number(make_get_request, es_write_data_genres):
    # Список genres
    response = await make_get_request(
        url=f"/api/v1/genres?page[number]=2&page[size]=15"
    )
    assert response.status == 200
    assert response.body["count"] == 26
    assert len(response.body["results"]) == 11
    assert response.body["results"][0]["id"] == "ca88141b-a6b4-450d-bbc3-efa940e4953f"
