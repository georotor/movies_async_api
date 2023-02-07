import pytest
from http import HTTPStatus


pytestmark = pytest.mark.asyncio


async def test_person(make_get_request, es_write_data_persons, es_write_data_movies):
    person_id = "189f1d17-c928-492a-aa33-2212b5ad1555"
    response = await make_get_request(url=f"/api/v1/persons/{person_id}")
    assert response.status == HTTPStatus.OK
    assert response.body["id"] == person_id
    assert response.body["name"] == "Gareth Edwards"


async def test_person_notfound(make_get_request, es_write_data_persons, es_write_data_movies):
    person_id = "cadefb3c-948c-4363-9f34-864cbc6d00d0"
    response = await make_get_request(url=f"/api/v1/persons/{person_id}")
    assert response.status == HTTPStatus.NOT_FOUND


async def test_person_valid_id(make_get_request, es_write_data_persons, es_write_data_movies):
    person_id = "189f1d7-c92-49a-aa3-222b5ad1555"
    response = await make_get_request(url=f"/api/v1/persons/{person_id}")
    assert response.status == HTTPStatus.UNPROCESSABLE_ENTITY


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


async def test_persons_next(make_get_request, es_write_data_persons):
    response = await make_get_request(url=f"/api/v1/persons")
    page_next = response.body["next"]

    response = await make_get_request(url=f"/api/v1/persons?page[next]={page_next}")
    assert response.status == HTTPStatus.OK
    assert len(response.body["results"]) == 50
    assert response.body["results"][0]["id"] == "26b6e17c-dc91-48f2-98d5-43c6c237ed1f"


async def test_persons_page_size(make_get_request, es_write_data_persons):
    response = await make_get_request(url=f"/api/v1/persons?page[size]=100")
    assert response.status == HTTPStatus.OK
    assert len(response.body["results"]) == 100
    assert response.body["results"][0]["id"] == "2871f883-e001-4848-92d0-002adbdf2547"


async def test_persons_page_size_and_next(make_get_request, es_write_data_persons):
    response = await make_get_request(url=f"/api/v1/persons?page[size]=100")
    assert len(response.body["results"]) == 100
    page_next = response.body["next"]

    response = await make_get_request(url=f"/api/v1/persons?page[next]={page_next}")
    assert response.status == HTTPStatus.OK
    assert len(response.body["results"]) == 50
    assert response.body["results"][0]["id"] == "e6ae9c81-aa7a-44b6-87ab-c63a2e298504"


async def test_search_page_size_and_next(make_get_request, es_write_data_persons):
    response = await make_get_request(
        url=f"/api/v1/persons/search?query=carl&page[size]=20"
    )
    assert len(response.body["results"]) == 4
    assert response.body["results"][0]["id"] == "858c3dfd-7f92-42a0-a916-047fb2babb36"


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
