from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models.database import User
from app.models.dto import UserReadDTO, UserCreateDTO
from app.repositories.interference import AbstractUserRepository


class UserRepository:
    """
    SQLAlchemy implementation of the User repository.
    
    This repository handles user creation and updates using PostgreSQL's
    UPSERT (INSERT ... ON CONFLICT DO UPDATE) to ensure that we always
    have the latest user data from Telegram.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[UserReadDTO]:
        """Fetch a user by their Telegram ID."""
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        return UserReadDTO.model_validate(user) if user else None

    async def upsert(self, user_data: UserCreateDTO) -> UserReadDTO:
        """
        Create a new user or update existing one.
        
        In Telegram bots, users don't explicitly "register". They just send /start.
        We need to either create them in the database or update their username/first_name
        if it has changed. This method uses PostgreSQL's UPSERT to do this atomically.
        
        SQL equivalent:
        INSERT INTO users (id, username, first_name) 
        VALUES (123, 'john_doe', 'John')
        ON CONFLICT (id) DO UPDATE 
        SET username = EXCLUDED.username, first_name = EXCLUDED.first_name
        """
        # Build the INSERT statement with ON CONFLICT clause
        stmt = pg_insert(User).values(
            id=user_data.id,
            username=user_data.username,
            first_name=user_data.first_name
        ).on_conflict_do_update(
            index_elements=['id'],  # Conflict target
            set_={
                'username': stmt.excluded.username,
                'first_name': stmt.excluded.first_name,
                # Note: we don't update created_at
            }
        ).returning(User)
        
        result = await self.session.execute(stmt)
        user = result.scalar_one()
        
        return UserReadDTO.model_validate(user)