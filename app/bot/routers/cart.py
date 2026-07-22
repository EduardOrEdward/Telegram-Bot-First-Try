from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.services.catalog import CatalogService
from app.services.order import OrderService
from app.services.uow import UnitOfWork
from app.bot.fsm.states import CartStates
from app.bot.fsm.callback_data import CartActionCallback, CheckoutCallback
from app.models.dto import OrderItemCreateDTO

router = Router()


@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery, state: FSMContext):
    """
    Handler for showing user's cart.
    
    Cart data is stored in FSM state.
    """
    # Get cart from FSM state
    data = await state.get_data()
    cart_items = data.get("cart", [])
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Your cart is empty.\n\n"
            "Browse the catalog to add items!"
        )
        return
    
    # Build cart text
    text = "🛒 Your Cart:\n\n"
    total = 0.0
    
    for item in cart_items:
        text += f"• {item['name']} × {item['quantity']} = ${item['price'] * item['quantity']}\n"
        total += item['price'] * item['quantity']
    
    text += f"\n💰 Total: ${total}"
    
    # Build keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Checkout",
            callback_data=CheckoutCallback(confirm=True).pack()
        )],
        [InlineKeyboardButton(
            text="🗑 Clear Cart",
            callback_data=CartActionCallback(action="clear", product_id=0).pack()
        )],
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(CartStates.viewing_cart)


@router.callback_query(CartActionCallback.filter())
async def handle_cart_action(
    callback: CallbackQuery,
    callback_data: CartActionCallback,
    state: FSMContext
):
    """
    Handler for cart actions (add, remove, increase, decrease, clear).
    """
    action = callback_data.action
    product_id = callback_data.product_id
    
    # Get current cart from FSM
    data = await state.get_data()
    cart = data.get("cart", [])
    
    if action == "add":
        # Fetch product details
        async with UnitOfWork() as uow:
            catalog_service = CatalogService(uow)
            product = await catalog_service.get_product_by_id(product_id)
        
        if not product:
            await callback.answer("❌ Product not found", show_alert=True)
            return
        
        if product.stock == 0:
            await callback.answer("❌ Product out of stock", show_alert=True)
            return
        
        # Check if product already in cart
        existing_item = next((item for item in cart if item['product_id'] == product_id), None)
        
        if existing_item:
            existing_item['quantity'] += 1
        else:
            cart.append({
                'product_id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': 1
            })
        
        await callback.answer("✅ Added to cart!")
    
    elif action == "clear":
        cart = []
        await callback.answer("🗑 Cart cleared!")
    
    # Save updated cart to FSM
    await state.update_data(cart=cart)
    
    # Refresh cart view
    await show_cart(callback, state)


@router.callback_query(CheckoutCallback.filter(), CartStates.viewing_cart)
async def checkout(
    callback: CallbackQuery,
    callback_data: CheckoutCallback,
    state: FSMContext,
    user
):
    """
    Handler for checkout confirmation.
    """
    if not callback_data.confirm:
        await callback.answer("Checkout cancelled")
        return
    
    # Get cart from FSM
    data = await state.get_data()
    cart_items = data.get("cart", [])
    
    if not cart_items:
        await callback.answer("Cart is empty", show_alert=True)
        return
    
    # Convert cart to OrderItemCreateDTO
    items = [
        OrderItemCreateDTO(product_id=item['product_id'], quantity=item['quantity'])
        for item in cart_items
    ]
    
    try:
        # Create order
        async with UnitOfWork() as uow:
            order_service = OrderService(uow)
            order = await order_service.create_order(user_id=user.id, items=items)
        
        # Clear cart
        await state.update_data(cart=[])
        
        await callback.message.edit_text(
            f"✅ Order #{order.id} created successfully!\n\n"
            f"💰 Total: ${order.total_amount}\n"
            f"📦 Items: {len(order.items)}\n\n"
            f"Thank you for your purchase!"
        )
    
    except ValueError as e:
        await callback.message.edit_text(f"❌ Error: {e}")