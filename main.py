import asyncio
import logging
from urllib.parse import urlparse
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.redis import RedisStorage

# Imports for SOCKS/HTTP proxy support in aiohttp
from aiohttp_socks import ProxyConnector, ProxyType

from config import settings
from app.database.redis import get_redis_client
from app.bot.routers import start, catalog, cart
from app.bot.middlewares.user import UserMiddleware

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_proxy_connector(proxy_url: str) -> Optional[ProxyConnector]:
    """
    Parses the proxy URL and creates an aiohttp ProxyConnector.
    Supports both socks5:// and http:// schemes.
    """
    try:
        parsed = urlparse(proxy_url)
        
        # Determine proxy type based on scheme
        if parsed.scheme.startswith('socks5'):
            proxy_type = ProxyType.SOCKS5
        elif parsed.scheme.startswith('http'):
            proxy_type = ProxyType.HTTP
        else:
            logger.warning(f"Unsupported proxy scheme: {parsed.scheme}. Falling back to direct connection.")
            return None

        # Create connector with Remote DNS (rdns=True) to prevent DNS leaks
        connector = ProxyConnector(
            proxy_type=proxy_type,
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            rdns=True  # Crucial: resolves hostnames through the proxy server
        )
        logger.info(f"Successfully configured proxy connector for {parsed.hostname}:{parsed.port}")
        return connector
        
    except Exception as e:
        logger.error(f"Failed to parse proxy URL '{proxy_url}': {e}")
        return None


async def main():
    # 1. Configure network session (with or without proxy)
    if settings.BOT_PROXY:
        connector = get_proxy_connector(settings.BOT_PROXY)
        if connector:
            session = AiohttpSession(connector=connector)
        else:
            logger.warning("Invalid proxy configuration. Falling back to direct connection.")
            session = AiohttpSession()
    else:
        session = AiohttpSession()
        logger.info("No proxy configured. Using direct connection.")

    # 2. Initialize Bot with the configured session
    bot = Bot(token=settings.BOT_TOKEN, session=session)
    
    # 3. Setup Redis and Dispatcher
    redis = await get_redis_client()
    storage = RedisStorage(redis)
    dp = Dispatcher(storage=storage)
    
    # 4. Register middlewares and routers
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    
    logger.info("Bot started successfully!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await redis.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped gracefully.")