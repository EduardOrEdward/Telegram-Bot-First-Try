from aiogram.filters.callback_data import CallbackData


class CategoryCallback(CallbackData, prefix="category"):
    """Callback data for category selection."""
    id: int


class ProductCallback(CallbackData, prefix="product"):
    """Callback data for product selection."""
    id: int


class CartActionCallback(CallbackData, prefix="cart"):
    """Callback data for cart actions."""
    action: str  # "add", "remove", "increase", "decrease", "clear"
    product_id: int


class CheckoutCallback(CallbackData, prefix="checkout"):
    """Callback data for checkout confirmation."""
    confirm: bool  # True = confirm, False = cancel