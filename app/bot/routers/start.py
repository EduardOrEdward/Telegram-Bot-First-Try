from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from app.models.dto import UserReadDTO

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user: UserReadDTO):
    """
    Handler for /start command.
    
    This is the entry point for new users.
    The user is automatically registered by UserMiddleware.
    
    Args:
        message: Telegram message
        user: User DTO (injected by middleware)
    """
    # Build main menu keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Catalog", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 My Cart", callback_data="cart")],
        [InlineKeyboardButton(text="📦 My Orders", callback_data="orders")],
    ])
    
    # Send welcome message
    await message.answer(
        f"Welcome to our shop, {user.first_name}! 🎉\n\n"
        f"What would you like to do?",
        reply_markup=keyboard
    )