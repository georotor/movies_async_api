import pytest
from http import HTTPStatus


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    'genre_id, answer',
    [
        ('120a21cf-9097-479e-904a-13dd7198c1dd', {'status': HTTPStatus.OK, 'name': 'Adventure'}),
        ('cadefb3c-948c-4363-9f34-864cbc6d00d0', {'status': HTTPStatus.NOT_FOUND}),
        ('20a21cf-997-49e-94a-13d7198c1dd', {'status': HTTPStatus.UNPROCESSABLE_ENTITY}),
    ]
)
async def test_genre(make_get_request, es_write_data_genres, genre_id, answer):
    response = await make_get_request(url=f"/api/v1/genres/{genre_id}")
    assert response.status == answer['status']
    if 'name' in answer:
        assert response.body["name"] == "Adventure"


async def test_genres(make_get_request, es_write_data_genres):
    response = await make_get_request(url=f"/api/v1/genres")
    assert response.status == HTTPStatus.OK
    assert response.body["count"] == 26
    assert len(response.body["results"]) == 10
    assert response.body["results"][0]["id"] == "3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff"
