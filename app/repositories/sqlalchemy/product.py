from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.database import Product
from app.models.dto import ProductReadDTO
from app.repositories.interference import AbstractProductRepository
from sqlalchemy.orm import selectinload

class ProductRepository:
    """
    SQLAlchemy implementation of the Product repository.
    
    This repository handles product queries and stock management.
    The `decrease_stock` method uses atomic UPDATE to prevent race conditions.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: int) -> Optional[ProductReadDTO]:
        """
        Fetch a single product by its ID.
        
        We eagerly load the category relationship to avoid DetachedInstanceError
        when converting to DTO after the session is closed.
        """
        query = (
            select(Product)
            .where(Product.product_id == product_id)
            # Eagerly load category to populate category_name in DTO
            .options(selectinload(Product.category))
        )
        result = await self.session.execute(query)
        product = result.scalar_one_or_none()
        
        if product is None:
            return None
        
        # Convert ORM model to DTO
        product_dto = ProductReadDTO.model_validate(product)
        
        # Manually populate denormalized field from the loaded relationship
        if product.category:
            product_dto.category_name = product.category.name
        
        return product_dto

    async def get_by_category(self, category_id: int) -> List[ProductReadDTO]:
        """
        Fetch all products within a specific category.
        
        This is used when a user clicks on a category in the catalog.
        """
        query = (
            select(Product)
            .where(Product.category_id == category_id)
            .order_by(Product.name)
        )
        result = await self.session.execute(query)
        products = result.scalars().all()
        
        return [ProductReadDTO.model_validate(p) for p in products]

    async def decrease_stock(self, product_id: int, quantity: int) -> bool:
        """
        Atomically decrease product stock.
        
        This method uses an UPDATE query with a WHERE clause to ensure that
        we only decrease stock if there are enough items available.
        This prevents race conditions when multiple users try to buy
        the same product simultaneously.
        
        SQL equivalent:
        UPDATE products 
        SET stock = stock - :quantity 
        WHERE id = :product_id AND stock >= :quantity
        
        Returns True if the stock was successfully decreased, False otherwise.
        """
        query = (
            update(Product)
            .where(Product.product_id == product_id, Product.stock >= quantity)
            .values(stock=Product.stock - quantity)
            .returning(Product.product_id)
        )
        result = await self.session.execute(query)
        
        # If rowcount > 0, the update succeeded (stock was sufficient)
        return result.rowcount > 0