from aiogram.fsm.state import State, StatesGroup


class CatalogStates(StatesGroup):
    """States for catalog browsing flow."""
    viewing_categories = State()  # User is viewing category list
    viewing_products = State()  # User is viewing products in a category
    viewing_product = State()  # User is viewing product details


class CartStates(StatesGroup):
    """States for cart management flow."""
    viewing_cart = State()  # User is viewing their cart
    checkout = State()  # User is confirming checkout


class OrderStates(StatesGroup):
    """States for order creation flow."""
    confirming_order = State()  # User is confirming order details
    order_created = State()  # Order successfully created