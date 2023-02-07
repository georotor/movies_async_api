from dataclasses import dataclass

import aiohttp
import pytest
from multidict import CIMultiDictProxy

from tests.functional.settings import test_settings


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


@pytest.fixture(scope='session')
async def session():
    """ Единая сессия для всех тестов. """
    client_session = aiohttp.ClientSession()
    yield client_session
    await client_session.close()


@pytest.fixture
def make_get_request(session):
    """
    Фикстура для выполнения GET запросов.

    :param session: Клиент aiohttp.
    :return: Функция выполнения GET запросов.
    """
    async def inner(url: str, params: dict | None = None):
        """
        Фикстура для выполнения GET запросов к API
        :param url: URL запроса.
        :param params: Словарь с параметрами для запроса.
        :return: Ответ в виде HTTPResponse объекта.
        """
        params = params or {}
        url = test_settings.service_url + url
        async with session.get(url, params=params) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )
    return inner
