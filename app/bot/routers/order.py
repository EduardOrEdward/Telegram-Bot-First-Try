# app/bot/routers/order.py
from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.services.order import OrderService
from app.services.uow import UnitOfWork
from app.models.dto import OrderItemCreateDTO

router = Router()

@router.callback_query(F.data.startswith("checkout_"))
async def checkout(callback: CallbackQuery):
    """Handler for creating an order."""
    # Parse cart items from callback data (simplified example)
    # In real app, you'd use FSM or Redis to store cart
    cart_items = [
        OrderItemCreateDTO(id=1, quantity=2),
        OrderItemCreateDTO(id=3, quantity=1),
    ]
    
    try:
        async with UnitOfWork() as uow:
            order_service = OrderService(uow)
            
            # Create order atomically
            order = await order_service.create_order(
                user_id=callback.from_user.id,
                items=cart_items
            )
        
        await callback.message.answer(
            f"✅ Order #{order.id} created!\n"
            f"Total: ${order.total_amount}"
        )
    except ValueError as e:
        # Handle business logic errors (out of stock, etc.)
        await callback.message.answer(f"Error: {e}")