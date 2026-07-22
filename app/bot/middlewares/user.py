from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.services.user import UserService
from app.services.uow import UnitOfWork


class UserMiddleware(BaseMiddleware):
    """
    Middleware for automatic user registration/update.
    
    This middleware runs on every message/callback and:
    1. Extracts user data from Telegram update
    2. Creates or updates user in database
    3. Attaches user object to the event data
    
    Why middleware instead of calling in each handler?
    - Eliminates code duplication
    - Guarantees user is always registered
    - Provides user object to all handlers automatically
    
    Usage in handlers:
        @router.message()
        async def handler(message: Message, user: UserReadDTO):
            # user is automatically injected by middleware
            await message.answer(f"Hello, {user.first_name}!")
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Middleware entry point.
        
        Args:
            handler: Next handler in the chain
            event: Telegram update (Message, CallbackQuery, etc.)
            data: Event data dictionary
        
        Returns:
            Handler result
        """
        # Extract user data based on event type
        telegram_user = None
        if isinstance(event, Message):
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user
        
        # If we have user data, register/update them
        if telegram_user:
            async with UnitOfWork() as uow:
                user_service = UserService(uow)
                user = await user_service.get_or_create_user(
                    user_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name
                )
                # Attach user to event data for handlers to use
                data["user"] = user
        
        # Call the next handler
        return await handler(event, data)