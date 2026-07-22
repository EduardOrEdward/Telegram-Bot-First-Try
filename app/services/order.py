from typing import List
from decimal import Decimal
from app.models.dto import OrderReadDTO, OrderItemCreateDTO
from app.services.uow import UnitOfWork


class OrderService:
    """
    Service for order-related business logic.
    
    This service handles order creation, retrieval, and management.
    It encapsulates critical business rules such as:
    - Stock availability checks
    - Price freezing at the moment of purchase
    - Atomic order creation with stock deduction
    - Order total calculation
    
    Why is this the most complex service?
    - It involves multiple entities (Order, OrderItem, Product)
    - It requires atomic transactions (all or nothing)
    - It handles race conditions (concurrent purchases)
    - It freezes prices (business-critical for accounting)
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize OrderService with a UnitOfWork instance.
        
        We inject UoW because order creation is a multi-step transaction
        that must be atomic. The UoW ensures that either all operations
        succeed or all are rolled back.
        """
        self.uow = uow

    async def create_order(
        self,
        user_id: int,
        items: List[OrderItemCreateDTO]
    ) -> OrderReadDTO:
        """
        Create a new order atomically.
        
        This is the most critical method in the entire application.
        It must handle:
        1. Validate that all products exist
        2. Check stock availability for each product
        3. Deduct stock atomically (prevent race conditions)
        4. Freeze prices at the moment of purchase
        5. Calculate total amount
        6. Create Order and OrderItem records
        7. Commit transaction (or rollback on any error)
        
        Business rules:
        - If any product is out of stock → rollback entire order
        - Prices are frozen at the moment of purchase (not current prices)
        - Stock deduction is atomic (no overselling)
        - Order total is calculated from frozen prices
        
        Why use UnitOfWork here?
        - Multiple database operations must be atomic
        - If stock deduction fails, we must rollback order creation
        - If order creation fails, we must rollback stock deduction
        - UoW ensures consistency and prevents partial updates
        
        Args:
            user_id: Telegram user ID
            items: List of items to order (product_id, quantity)
        
        Returns:
            OrderReadDTO with the created order
        
        Raises:
            ValueError: If any product is not found or out of stock
        """
        # Validate input
        if not items:
            raise ValueError("Order must contain at least one item")
        
        # Delegate to repository for atomic order creation
        # The repository handles:
        # - Locking products (SELECT ... FOR UPDATE)
        # - Checking stock availability
        # - Deducting stock atomically
        # - Creating Order and OrderItem records
        # - Freezing prices
        # - Calculating total amount
        order = await self.uow.orders.create(user_id=user_id, items=items)
        
        return order

    async def get_order_by_id(self, order_id: int) -> OrderReadDTO:
        """
        Get a specific order by ID.
        
        This is useful for showing order details to the user.
        
        Business rules:
        - Return order with all items
        - Include frozen prices (not current prices)
        
        Args:
            order_id: Order ID
        
        Returns:
            OrderReadDTO if order exists, None otherwise
        """
        order = await self.uow.orders.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        return order

    async def get_user_orders(self, user_id: int) -> List[OrderReadDTO]:
        """
        Get all orders for a specific user.
        
        This is called when a user wants to see their order history.
        
        Business rules:
        - Return all orders for the user
        - Orders are ordered by creation date (newest first)
        - Include order items with frozen prices
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            List of OrderReadDTO
        """
        orders = await self.uow.orders.get_user_orders(user_id)
        return orders

    async def calculate_cart_total(
        self,
        items: List[OrderItemCreateDTO]
    ) -> Decimal:
        """
        Calculate the total amount for a cart (before creating order).
        
        This is useful for showing the user the total before they confirm.
        
        Business rules:
        - Use current prices (not frozen, as order is not yet created)
        - Check stock availability
        - Return total as Decimal (for precision)
        
        Why separate from create_order?
        - Allows showing total before confirmation
        - No side effects (doesn't create order or deduct stock)
        - Can be called multiple times without consequences
        
        Args:
            items: List of items in cart (product_id, quantity)
        
        Returns:
            Total amount as Decimal
        
        Raises:
            ValueError: If any product is not found or out of stock
        """
        total = Decimal("0.00")
        
        for item in items:
            # Fetch product to get current price and stock
            product = await self.uow.products.get_by_id(item.id)
            if not product:
                raise ValueError(f"Product {item.id} not found")
            
            if product.stock < item.quantity:
                raise ValueError(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.stock}, Requested: {item.quantity}"
                )
            
            # Add to total
            total += product.price * item.quantity
        
        return total