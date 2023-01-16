from aioredis import Redis

from src.services.cache_managers.abstract_manager import AbstractManager


class RedisManager(AbstractManager):
    """Реализация AbstractManager для работы с aioredis. Наследует метод
    create_id для создания хэш-ключа.

    """
    def __init__(self, redis: Redis, ttl: int = 300):
        """
        Args:
          redis: инициализированный объект aioredis;
          ttl: жизнь ключа в секундах, устанавливается через redis.expire().

        """
        self.redis = redis
        self.ttl = ttl

    async def get(self, cash_id: str):
        """Ищем объект в кэше."""
        return await self.redis.get(cash_id) or None

    async def put(self, cash_id, data):
        """Записываем данные в кэш."""
        await self.redis.set(cash_id, data)
        await self.redis.expire(cash_id, self.ttl)

    async def delete(self, cash_id):
        """Удаляем данные."""
        await self.redis.delete(cash_id)