import pytest
from http import HTTPStatus


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    'person_id, answer',
    [
        ('189f1d17-c928-492a-aa33-2212b5ad1555', {'status': HTTPStatus.OK, 'name': 'Gareth Edwards'}),
        ('cadefb3c-948c-4363-9f34-864cbc6d00d0', {'status': HTTPStatus.NOT_FOUND}),
        ('189f1d7-c92-49a-aa3-222b5ad1555', {'status': HTTPStatus.UNPROCESSABLE_ENTITY}),
    ]
)
async def test_person(make_get_request, es_write_data_persons, es_write_data_movies, person_id, answer):
    response = await make_get_request(url=f"/api/v1/persons/{person_id}")
    assert response.status == answer['status']
    if 'name' in answer:
        assert response.body["name"] == answer['name']


async def test_persons(make_get_request, es_write_data_persons):
    response = await make_get_request(url=f"/api/v1/persons")

    assert response.status == HTTPStatus.OK
    assert response.body["count"] == 4166
    assert (
        response.body["next"]
        == "WyJBaWRhbiBTY290dCIsImI3NThiNGQzLTczMGYtNDkxYS1hYTcxLTM5MDBlNGJmMWY2ZSJd"
    )
    assert len(response.body["results"]) == 50
    assert response.body["results"][0]["id"] == "2871f883-e001-4848-92d0-002adbdf2547"


@pytest.mark.parametrize(
    "params, answer",
    [
        (
            {"query": "arthur", "page[size]": 100},
            {
                "count": 11,
                "results": 11,
                "id": "c6c9231f-45ce-4751-8775-858b7b00f8ca",
            },
        ),
        (
            {"query": "pavel"},
            {
                "count": 2,
                "results": 2,
                "id": "b9c52ab2-4336-4ff8-9a4b-40272077902f",
            },
        ),
        (
            {"query": "constantine"},
            {
                "count": 1,
                "results": 1,
                "id": "092ef447-4f99-4c51-97fc-83213fbd9cc1",
            },
        ),
    ],
)
async def test_persons_search(make_get_request, es_write_data_persons, params, answer):
    response = await make_get_request(url=f"/api/v1/persons/search", params=params)

    assert response.status == HTTPStatus.OK
    assert response.body["count"] == answer["count"]
    assert len(response.body["results"]) == answer["results"]
    if "id" in answer:
        assert response.body["results"][0]["id"] == answer["id"]


@pytest.mark.parametrize(
    "params, answer",
    [
        (
            {"person_id": "05572526-d39e-483f-b548-92ebda7702eb"},
            {
                "count": 1,
                "film_id": "b2ddce38-9689-4a33-8dd6-7efd2411ed2d",
                "title": "Star of India",
            },
        ),
    ],
)
async def test_person_film(make_get_request, es_write_data_persons, es_write_data_movies, params, answer):
    response = await make_get_request(url=f"/api/v1/persons/{params['person_id']}/film")

    assert response.status == HTTPStatus.OK
    assert response.body["count"] == answer["count"]
    if response.body["count"] > 0:
        assert response.body["results"][0]["id"] == answer["film_id"]
        assert response.body["results"][0]["title"] == answer["title"]


async def test_person_film_notfound(make_get_request, es_write_data_persons, es_write_data_movies):
    person_id = "05572526-d39e-483f-b548-92ebda7702ee"
    response = await make_get_request(url=f"/api/v1/persons/{person_id}/film")
    assert response.status == HTTPStatus.NOT_FOUND
