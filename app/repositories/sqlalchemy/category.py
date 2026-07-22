from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.database import Category
from app.models.dto import CategoryReadDTO
from app.repositories.interference import AbstractCategoryRepository


class CategoryRepository:
    """
    SQLAlchemy implementation of the Category repository.
    
    Categories are typically static data that doesn't change often.
    In a real production system, you would cache these in Redis
    to avoid hitting PostgreSQL on every catalog view.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[CategoryReadDTO]:
        """
        Fetch all available categories.
        
        This is typically used to build inline keyboards in Telegram.
        For better performance, consider caching this in Redis.
        """
        query = select(Category).order_by(Category.name)
        result = await self.session.execute(query)
        categories = result.scalars().all()
        
        return [CategoryReadDTO.model_validate(cat) for cat in categories]

    async def get_by_id(self, category_id: int) -> Optional[CategoryReadDTO]:
        """Fetch a single category by ID."""
        query = select(Category).where(Category.category_id == category_id)
        result = await self.session.execute(query)
        category = result.scalar_one_or_none()
        
        return CategoryReadDTO.model_validate(category) if category else None