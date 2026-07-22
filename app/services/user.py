from typing import Optional
from app.models.dto import UserReadDTO, UserCreateDTO
from app.services.uow import UnitOfWork


class UserService:
    """
    Service for user-related business logic.
    
    This service handles user registration, updates, and retrieval.
    It encapsulates all business rules related to users, such as:
    - Automatic user creation on first interaction (upsert)
    - User data synchronization with Telegram
    - User existence checks
    
    Why separate from handlers?
    - Reusability: Can be called from different handlers or even non-Telegram contexts
    - Testability: Can be tested without Aiogram mocks
    - Single Responsibility: Handlers handle Telegram, UserService handles users
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize UserService with a UnitOfWork instance.
        
        We inject UoW (not individual repositories) because:
        1. All operations in this service should be atomic
        2. It's easier to manage transactions at the service level
        3. The service might need multiple repositories in the future
        """
        self.uow = uow

    async def get_or_create_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str
    ) -> UserReadDTO:
        """
        Get existing user or create a new one.
        
        This is the primary method called on every /start or message.
        It ensures that we always have the latest user data from Telegram.
        
        Business rules:
        1. If user doesn't exist → create new user
        2. If user exists → update username and first_name
        3. Return the (possibly updated) user
        
        Why upsert instead of separate get/create?
        - Atomic operation (no race conditions)
        - Single database round-trip (better performance)
        - Simpler code (no need to check existence first)
        
        Args:
            user_id: Telegram user ID (unique identifier)
            username: Telegram username (can be None)
            first_name: User's first name (required by Telegram)
        
        Returns:
            UserReadDTO with the latest user data
        """
        # Prepare user data for upsert
        user_data = UserCreateDTO(
            id=user_id,
            username=username,
            first_name=first_name
        )
        
        # Perform upsert atomically
        # The repository handles INSERT ... ON CONFLICT DO UPDATE
        user = await self.uow.users.upsert(user_data)
        
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[UserReadDTO]:
        """
        Get user by Telegram ID without creating if not exists.
        
        This is useful when we need to check if a user exists
        without side effects (e.g., before showing order history).
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            UserReadDTO if user exists, None otherwise
        """
        user = await self.uow.users.get_by_id(user_id)
        return user