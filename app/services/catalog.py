from typing import List, Optional
from app.models.dto import CategoryReadDTO, ProductReadDTO
from app.services.uow import UnitOfWork


class CatalogService:
    """
    Service for catalog-related business logic.
    
    This service handles browsing categories and products.
    It encapsulates business rules such as:
    - Category listing for inline keyboards
    - Product filtering by category
    - Product detail retrieval
    
    Why separate from handlers?
    - Catalog logic can be reused (e.g., in admin panel, web interface)
    - Easier to add caching later (Redis) without touching handlers
    - Business rules (e.g., "show only in-stock products") are centralized
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize CatalogService with a UnitOfWork instance.
        
        Note: Catalog operations are read-only, so we don't need
        transaction management. However, we still use UoW for consistency
        and to access repositories.
        """
        self.uow = uow

    async def get_all_categories(self) -> List[CategoryReadDTO]:
        """
        Get all available categories.
        
        This is typically used to build inline keyboards in Telegram.
        
        Business rules:
        - Return all categories (no filtering for now)
        - Categories are ordered by name (handled by repository)
        
        Future enhancements:
        - Add Redis caching (categories rarely change)
        - Add filtering (e.g., only categories with products)
        
        Returns:
            List of CategoryReadDTO
        """
        categories = await self.uow.categories.get_all()
        return categories

    async def get_category_by_id(self, category_id: int) -> Optional[CategoryReadDTO]:
        """
        Get a single category by ID.
        
        This is useful when we need to validate that a category exists
        before showing its products.
        
        Args:
            category_id: Category ID
        
        Returns:
            CategoryReadDTO if category exists, None otherwise
        """
        category = await self.uow.categories.get_by_id(category_id)
        return category

    async def get_products_by_category(self, category_id: int) -> List[ProductReadDTO]:
        """
        Get all products within a specific category.
        
        This is called when a user clicks on a category in the catalog.
        
        Business rules:
        - Return all products in the category (including out-of-stock)
        - Products are ordered by name (handled by repository)
        - Include category_name in DTO for display purposes
        
        Future enhancements:
        - Add pagination (if category has many products)
        - Add filtering (e.g., only in-stock products)
        - Add sorting options (by price, name, etc.)
        
        Args:
            category_id: Category ID
        
        Returns:
            List of ProductReadDTO
        """
        # Validate that category exists
        category = await self.uow.categories.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")
        
        # Fetch products
        products = await self.uow.products.get_by_category(category_id)
        return products

    async def get_product_by_id(self, product_id: int) -> Optional[ProductReadDTO]:
        """
        Get a single product by ID.
        
        This is called when a user clicks on a product to see details.
        
        Business rules:
        - Return product with full details (including category_name)
        - Include stock information for display
        
        Args:
            product_id: Product ID
        
        Returns:
            ProductReadDTO if product exists, None otherwise
        """
        product = await self.uow.products.get_by_id(product_id)
        return product