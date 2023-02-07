import redis.asyncio as aioredis
import pytest

from tests.functional.settings import test_settings


@pytest.fixture(scope='function')
async def redis_client():
    client = await aioredis.from_url(
        f"redis://{test_settings.redis_host}:{test_settings.redis_port}",
        encoding="utf8",
        decode_responses=True
    )
    yield client
    await client.close()
