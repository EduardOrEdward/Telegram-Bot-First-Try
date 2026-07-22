from redis.asyncio import Redis, ConnectionPool
from config import settings


class RedisClient:
    """
    Redis client wrapper for caching and FSM storage.
    
    This class provides a centralized way to interact with Redis.
    It uses connection pooling for better performance.
    
    Why separate class instead of direct Redis usage?
    - Centralized configuration
    - Easier to mock in tests
    - Can add retry logic, metrics, etc. later
    """

    def __init__(self):
        """Initialize Redis connection pool."""
        self.pool = ConnectionPool.from_url(
            str(settings.REDIS_DSN),
            decode_responses=True,  # Automatically decode bytes to strings
            max_connections=50,  # Limit connections to prevent overload
        )
        self.client = Redis(connection_pool=self.pool)

    async def close(self):
        """Close Redis connection pool on shutdown."""
        await self.client.close()
        await self.pool.disconnect()


# Global Redis client instance
redis_client = RedisClient()


async def get_redis_client() -> Redis:
    """
    Dependency for getting Redis client.
    
    This is used by Aiogram FSM storage and cache service.
    """
    return redis_client.client