from redis.asyncio.client import Redis


redis: Redis | None = None


# Функция понадобится при внедрении зависимостей
async def get_redis() -> Redis:
    return redis
