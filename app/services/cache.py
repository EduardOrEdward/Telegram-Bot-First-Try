import json
from typing import Optional, List, Any
from redis.asyncio import Redis
from app.database.redis import get_redis_client
from app.models.dto import CategoryReadDTO, ProductReadDTO


class CacheService:
    """
    Service for caching data in Redis.
    
    This service handles caching of frequently accessed data
    to reduce database load and improve response times.
    
    Cache keys format:
    - category:{id} - Single category
    - categories:all - All categories
    - products:category:{category_id} - Products in a category
    - product:{id} - Single product
    
    TTL (Time To Live):
    - Categories: 1 hour (rarely change)
    - Products: 5 minutes (change more often)
    """

    # Cache TTL in seconds
    CATEGORY_TTL = 3600  # 1 hour
    PRODUCT_TTL = 300  # 5 minutes

    def __init__(self, redis: Redis):
        """Initialize cache service with Redis client."""
        self.redis = redis

    # ==========================================
    # Category Cache
    # ==========================================

    async def get_all_categories(self) -> Optional[List[CategoryReadDTO]]:
        """
        Get all categories from cache.
        
        Returns:
            List of CategoryReadDTO if found in cache, None otherwise
        """
        data = await self.redis.get("categories:all")
        if data:
            categories_data = json.loads(data)
            return [CategoryReadDTO.model_validate(cat) for cat in categories_data]
        return None

    async def set_all_categories(self, categories: List[CategoryReadDTO]) -> None:
        """
        Cache all categories.
        
        Args:
            categories: List of categories to cache
        """
        categories_data = [cat.model_dump() for cat in categories]
        await self.redis.set(
            "categories:all",
            json.dumps(categories_data, default=str),  # default=str for datetime
            ex=self.CATEGORY_TTL
        )

    async def invalidate_categories(self) -> None:
        """
        Invalidate all categories cache.
        
        Call this when categories are added/updated/deleted.
        """
        await self.redis.delete("categories:all")

    # ==========================================
    # Product Cache
    # ==========================================

    async def get_products_by_category(self, category_id: int) -> Optional[List[ProductReadDTO]]:
        """
        Get products by category from cache.
        
        Args:
            category_id: Category ID
        
        Returns:
            List of ProductReadDTO if found in cache, None otherwise
        """
        data = await self.redis.get(f"products:category:{category_id}")
        if data:
            products_data = json.loads(data)
            return [ProductReadDTO.model_validate(prod) for prod in products_data]
        return None

    async def set_products_by_category(self, category_id: int, products: List[ProductReadDTO]) -> None:
        """
        Cache products by category.
        
        Args:
            category_id: Category ID
            products: List of products to cache
        """
        products_data = [prod.model_dump() for prod in products]
        await self.redis.set(
            f"products:category:{category_id}",
            json.dumps(products_data, default=str),
            ex=self.PRODUCT_TTL
        )

    async def invalidate_products_by_category(self, category_id: int) -> None:
        """
        Invalidate products cache for a specific category.
        
        Call this when products are added/updated/deleted in a category.
        
        Args:
            category_id: Category ID
        """
        await self.redis.delete(f"products:category:{category_id}")

    async def get_product_by_id(self, product_id: int) -> Optional[ProductReadDTO]:
        """
        Get single product from cache.
        
        Args:
            product_id: Product ID
        
        Returns:
            ProductReadDTO if found in cache, None otherwise
        """
        data = await self.redis.get(f"product:{product_id}")
        if data:
            product_data = json.loads(data)
            return ProductReadDTO.model_validate(product_data)
        return None

    async def set_product_by_id(self, product: ProductReadDTO) -> None:
        """
        Cache single product.
        
        Args:
            product: Product to cache
        """
        await self.redis.set(
            f"product:{product.id}",
            json.dumps(product.model_dump(), default=str),
            ex=self.PRODUCT_TTL
        )