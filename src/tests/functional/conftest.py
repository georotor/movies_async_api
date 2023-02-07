import asyncio
import pytest


pytest_plugins = ("utils.fixtures.elastic", "utils.fixtures.redis", "utils.fixtures.http")


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


