from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.services.catalog import CatalogService
from app.services.cache import CacheService
from app.services.uow import UnitOfWork
from app.bot.fsm.states import CatalogStates
from app.bot.fsm.callback_data import CategoryCallback, ProductCallback
from app.database.redis import get_redis_client

router = Router()


@router.callback_query(F.data == "catalog")
async def show_categories(callback: CallbackQuery, state: FSMContext):
    """
    Handler for showing all categories.
    
    This handler:
    1. Checks cache for categories
    2. If not in cache, fetches from database and caches
    3. Builds inline keyboard with categories
    """
    # Get Redis client for cache
    redis = await get_redis_client()
    cache = CacheService(redis)
    
    # Try to get categories from cache
    categories = await cache.get_all_categories()
    
    if not categories:
        # Not in cache, fetch from database
        async with UnitOfWork() as uow:
            catalog_service = CatalogService(uow)
            categories = await catalog_service.get_all_categories()
        
        # Cache the result
        await cache.set_all_categories(categories)
    
    # Build inline keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=cat.name,
            callback_data=CategoryCallback(id=cat.id).pack()
        )]
        for cat in categories
    ])
    
    # Update message and set state
    await callback.message.edit_text(
        "📂 Choose a category:",
        reply_markup=keyboard
    )
    await state.set_state(CatalogStates.viewing_categories)


@router.callback_query(CategoryCallback.filter(), CatalogStates.viewing_categories)
async def show_products(
    callback: CallbackQuery,
    callback_data: CategoryCallback,
    state: FSMContext
):
    """
    Handler for showing products in a category.
    
    This handler:
    1. Checks cache for products in category
    2. If not in cache, fetches from database and caches
    3. Builds inline keyboard with products
    """
    category_id = callback_data.id
    
    # Get Redis client for cache
    redis = await get_redis_client()
    cache = CacheService(redis)
    
    # Try to get products from cache
    products = await cache.get_products_by_category(category_id)
    
    if not products:
        # Not in cache, fetch from database
        async with UnitOfWork() as uow:
            catalog_service = CatalogService(uow)
            products = await catalog_service.get_products_by_category(category_id)
        
        # Cache the result
        await cache.set_products_by_category(category_id, products)
    
    if not products:
        await callback.message.edit_text("❌ No products in this category.")
        return
    
    # Build inline keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{prod.name} - ${prod.price}",
                callback_data=ProductCallback(id=prod.id).pack()
            )
        ]
        for prod in products
    ] + [
        [InlineKeyboardButton(text="🔙 Back", callback_data="catalog")]
    ])
    
    # Update message and set state
    await callback.message.edit_text(
        "🛍 Choose a product:",
        reply_markup=keyboard
    )
    await state.set_state(CatalogStates.viewing_products)


@router.callback_query(ProductCallback.filter(), CatalogStates.viewing_products)
async def show_product_details(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    state: FSMContext
):
    """
    Handler for showing product details.
    
    This handler shows full product information and adds to cart button.
    """
    product_id = callback_data.id
    
    async with UnitOfWork() as uow:
        catalog_service = CatalogService(uow)
        product = await catalog_service.get_product_by_id(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Product not found.")
        return
    
    # Build product details text
    text = (
        f"📦 {product.name}\n\n"
        f"📝 {product.description or 'No description'}\n\n"
        f"💰 Price: ${product.price}\n"
        f"📊 In stock: {product.stock}\n"
        f"📂 Category: {product.category_name}"
    )
    
    # Build keyboard with add to cart and back buttons
    from app.bot.fsm.callback_data import CartActionCallback
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛒 Add to Cart",
            callback_data=CartActionCallback(action="add", product_id=product.id).pack()
        )],
        [InlineKeyboardButton(text="🔙 Back", callback_data="catalog")],
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(CatalogStates.viewing_product)