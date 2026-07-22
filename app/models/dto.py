from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ==========================================
# Base Configuration
# ==========================================

class BaseDTO(BaseModel):
    """
    Base class for all DTOs.
    `from_attributes=True` (formerly `orm_mode` in Pydantic v1) allows Pydantic 
    to read data directly from ORM model instances (e.g., SQLAlchemy objects) 
    instead of just dictionaries.
    """
    model_config=ConfigDict(from_attributes=True)

# ==========================================
# User DTOs
# ==========================================

class UserReadDTO(BaseDTO):
    """DTO for reading user data from the database."""
    id:int
    username:Optional[str]=None
    first_name:str


class UserCreateDTO(BaseDTO):
    """DTO for creating/updating a user in the database."""
    id:int
    username:Optional[str]=None
    first_name:str

# ==========================================
# Category DTOs
# ==========================================

class CategoryReadDTO(BaseDTO):
    """DTO for reading category data."""
    id:int
    name:str
    description:Optional[str]=None

# ==========================================
# Product DTOs
# ==========================================

class ProductReadDTO(BaseDTO):
    """
    DTO for reading product data.
    We use `Decimal` for money to avoid floating-point precision issues.
    """
    id:int
    category_id:int
    name:str
    description:Optional[str]=None
    price:Decimal
    stock:int
    
    
    category_name:Optional[str]=None


class ProductCreateDTO(BaseDTO):
    """DTO for creating a new product."""
    id:int
    name:str
    description:Optional[str]=None
    price:Decimal
    stock:int = Field(default=0,ge=0)


# ==========================================
# Order Item DTOs
# ==========================================

class OrderItemReadDTO(BaseDTO):
    """DTO for reading a specific item within an order."""
    id:int
    product_id:int
    quantity:int
    price_at_purchase:Decimal
    
    # Denormalized data for easier display in UI (Telegram messages)
    product_name:Optional[str]=None


class OrderItemCreateDTO(BaseDTO):
    """DTO for adding an item to an order (used in business logic)."""
    id:int
    quantity:int=Field(default=1,ge=1)

# ==========================================
# Order DTOs
# ==========================================

class OrderReadDTO(BaseDTO):
    """DTO for reading order data with its items."""
    id:int
    user_id:int
    total_amount:Decimal
    status:str
    created_at:datetime
    
    # Nested DTOs. Pydantic will automatically validate and convert them.
    items:List[OrderItemReadDTO] = []

class OrderCreateDTO(BaseDTO):
    """DTO for initiating a new order."""
    user_id:int
    items:List[OrderItemCreateDTO]
