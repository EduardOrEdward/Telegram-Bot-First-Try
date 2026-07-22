from typing import Protocol, List, Optional,runtime_checkable
from app.models.dto import (UserReadDTO,UserCreateDTO,ProductReadDTO,OrderReadDTO,OrderItemCreateDTO,CategoryReadDTO)

# ==========================================
# User Repository Interface
# ==========================================

@runtime_checkable
class AbstractUserRepository(Protocol):
    """
    Contact for user data access.
    '@runtime_checkable' allows us to use 'isinstance(obj,AbstractUserRepository)'
    at runtime, which is useful for debuging
    """
    
    async def get_by_id(self,user_id:int)->Optional[UserReadDTO]:
        """Fetch a user by their Telegram ID"""
        ...
    async def upsert(self,user_data:UserCreateDTO)->UserReadDTO: #update + insert, since we can't make the Telegram user register, only either insert the user into Database or update their data(username,first_name)
        """
        Create a new user or update an existed one
        Essential for Telegram bots, as we need register/update users
        on every message or command
        """
        ...

# ==========================================
# Category Repository Interface
# ==========================================

class AbstractCategoryRepository(Protocol):
    """Contact for category data access"""
    
    async def get_all(self)->List[CategoryReadDTO]:
        """Fetch all availbe categories(e.g., for inline keyboards)"""
        ...
    async def get_by_id(self,cat_id)->Optional[CategoryReadDTO]:
        """Fetch a category by it`s ID"""
        ...


# ==========================================
# Product Repository Interface
# ==========================================

class AbstractProductRepository(Protocol):
    """Contact for product data access"""
    
    async def get_by_id(self,product_id:int)->Optional[ProductReadDTO]:
        """Fetch a specific product by it`s ID"""
        ...
    async def get_by_category(self,category_id:int)->List[CategoryReadDTO]:
        """Fetch all product by specific category ID"""
        ...
    async def decrease_stock(self,product_id:int,quanity:int)->bool: #Why bool? because if we do it manually -> stock=stock-1, we can get negative stock, so for this we use boolean proof that stock>= quanity, if it's true the function will return True, otherwise False and User won't be able to order a out of sale product
        """
        Automatically decrease stock of the product.
        Return True if there`s left(by that I mean that amount of product is ge than 1)
        Return False otherwise, preventing from race conditions in orders
        """
        ...


# ==========================================
# Order Repository Interface
# ==========================================

class AbstractOrderRepository(Protocol):
    """Contact for order data access"""
    
    async def create(
        self,
        user_id:int,
        items:List[OrderItemCreateDTO]
    ) -> OrderReadDTO:
        """
        Create a new order with specified items.
        The implementation must handle calculating the total amount,
        freezing prices and decreasing stock automatically
        """
        ...
    async def get_by_id(self,order_id:int)->Optional[OrderReadDTO]:
        """Fetch a specific order by it`s ID"""
        ...
    async def get_user_order(self,user_id:int)->List[OrderReadDTO]:
        """Fetch all orders for a specific user, ordered by creation date"""
        ...