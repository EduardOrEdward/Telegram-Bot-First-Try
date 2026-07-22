from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.database import Order, OrderItem, Product
from app.models.dto import OrderReadDTO, OrderItemCreateDTO
from app.repositories.interference import AbstractOrderRepository

class OrderRepository:
    """
    SQLAlchemy implementation of the Order repository.
    
    This repository handles atomic order creation with pessimistic locking
    to prevent race conditions when multiple users try to buy the same product.
    """
    
    def __init__(self,session:AsyncSession):
        self.session=session
    async def create(
        self,
        user_id:int,
        items:List[OrderItemCreateDTO]
    )->OrderReadDTO:
        """
        Create a new order atomically.
        
        Steps:
        1. Lock all products in the order (SELECT ... FOR UPDATE).
        2. Check if stock is sufficient for each product.
        3. Decrease stock for each product.
        4. Create Order and OrderItem records with frozen prices.
        5. Calculate total_amount.
        6. Return the created order as a DTO.
        
        If any step fails (e.g., insufficient stock), the entire transaction
        is rolled back by the UnitOfWork.
        """
        product_ids = [item.id for item in items]
        query = (
            select(Product)
            .where(Product.product_id.in_(product_ids))
            .with_for_update()  # Pessimistic lock: other transactions will wait
        )
        result = await self.session.execute(query)
        products = {p.product_id: p for p in result.scalars().all()}
        
        order_items_data = []
        total_amount = 0.0
        
        for item in items:
            product = products.get(item.id)
            if not product:
                raise ValueError(f"Product: {item.id} not found")
            
            if product.stock < item.quantity:
                raise ValueError(
                    f"Insufficient stock for product: {product.name}"
                    f"Available: {product.stock}, Requested: {item.quantity}")
            
            
            update_query = (
                update(Product)
                .where(Product.product_id== product.product_id, Product.stock >= item.quantity)
                .values(stock=Product.stock-item.quantity)
            )
            update_result = await self.session.execute(update_query)
            
            if update_result.rowcount == 0:
                
                raise ValueError(f"Failed to decrease stock for product: {product.product_id}")
            
            order_items_data.append({
                "product_id":product.product_id,
                "quanity":item.quantity,
                "price_at_purchase":product.price
            })
            
            total_amount+=product.price * item.quantity
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status="pending"
        )
        
        self.session.add(order)
        await self.session.flush()
        
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.orders_id,
                **item_data
            )
            self.session.add(order_item)
        
        final_query = (
            select(Order)
            .where(Order.orders_id==order.orders_id)
            .options(selectinload(Order.items))
        )
        final_result = await self.session.execute(final_query)
        created_order = final_result.scalar_one()
        return OrderReadDTO.model_validate(created_order)
    
    async def get_by_id(self,order_id:int)->Optional[OrderReadDTO]:
        
        query = (
            select(Order)
            .where(Order.orders_id==order_id)
            .options(selectinload(Order.items))
        )
        result = await self.session.execute(query)
        order = result.scalar_one_or_none()
        
        return OrderReadDTO.model_validate(order) if order else None
    
    async def get_user_orders(self,user_id:int)->List[OrderReadDTO]:
        query = (
            select(Order)
            .where(Order.user_id==user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        result = await self.session.execute(query)
        orders = result.scalars().all()
        return [OrderReadDTO.model_validate(order) for order in orders]
    