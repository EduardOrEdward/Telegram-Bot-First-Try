from typing import Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_factory
from app.repositories.sqlalchemy.user import UserRepository
from app.repositories.sqlalchemy.category import CategoryRepository
from app.repositories.sqlalchemy.product import ProductRepository
from app.repositories.sqlalchemy.order import OrderRepository


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing database transactions.
    
    This class ensures that all database operations within a business transaction
    use the same database session and are committed or rolled back atomically.
    
    Key responsibilities:
    1. Create and manage a single database session for all repositories
    2. Initialize all repositories with the shared session
    3. Handle transaction commit/rollback automatically
    4. Ensure proper session cleanup (return connection to pool)
    
    Usage:
        async with UnitOfWork() as uow:
            # All repositories share the same session
            user = await uow.users.upsert(user_data)
            order = await uow.orders.create(user_id=user.id, items=[...])
            # If no exception occurs, all changes are committed automatically
            # If an exception occurs, all changes are rolled back
    
    Why this pattern?
    - Separates transaction management from business logic
    - Ensures atomicity: all operations succeed or all fail
    - Prevents partial updates that could leave database in inconsistent state
    - Makes testing easier: you can mock the entire transaction
    """

    def __init__(self):
        """
        Initialize UnitOfWork.
        
        We don't create the session here because we want to defer it
        until __aenter__ is called. This allows for better resource management
        and prevents holding connections longer than necessary.
        """
        self._session: Optional[AsyncSession] = None
        self._session_factory = async_session_factory
        
        # Repositories will be initialized in __aenter__
        self.users: Optional[UserRepository] = None
        self.categories: Optional[CategoryRepository] = None
        self.products: Optional[ProductRepository] = None
        self.orders: Optional[OrderRepository] = None

    async def __aenter__(self) -> "UnitOfWork":
        """
        Enter the async context manager.
        
        This method:
        1. Creates a new database session from the factory
        2. Initializes all repositories with the shared session
        3. Returns self so repositories can be accessed as attributes
        
        The session is created here (not in __init__) to ensure that
        we don't hold database connections longer than necessary.
        """
        # Create a new session from the factory
        self._session = self._session_factory()
        
        # Initialize all repositories with the same session
        # This ensures all operations use the same transaction
        self.users = UserRepository(self._session)
        self.categories = CategoryRepository(self._session)
        self.products = ProductRepository(self._session)
        self.orders = OrderRepository(self._session)
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the async context manager.
        
        This method handles transaction commit/rollback and session cleanup.
        
        Logic:
        - If an exception occurred (exc_type is not None):
            Rollback all changes to maintain database consistency
        - If no exception occurred:
            Commit all changes to persist them to the database
        - Always close the session to return the connection to the pool
        
        Parameters:
        - exc_type: Exception type (None if no exception)
        - exc_val: Exception value (None if no exception)
        - exc_tb: Exception traceback (None if no exception)
        """
        try:
            if exc_type is not None:
                # An exception occurred - rollback all changes
                # This ensures database consistency
                await self._session.rollback()
            else:
                # No exception - commit all changes
                # This persists all changes made within the transaction
                await self._session.commit()
        finally:
            # Always close the session to release the connection back to the pool
            # This is critical for preventing connection leaks
            await self._session.close()

    @property
    def session(self) -> AsyncSession:
        """
        Get the current database session.
        
        This is useful when you need to access the session directly,
        for example, to execute raw SQL queries or perform operations
        that are not covered by repositories.
        
        Raises:
            RuntimeError: If called outside of the context manager
        """
        if self._session is None:
            raise RuntimeError(
                "Session is not initialized. "
                "Make sure you're using UnitOfWork within an async context manager."
            )
        return self._session

    async def commit(self) -> None:
        """
        Manually commit the current transaction.
        
        This is useful when you need to commit changes before the context manager exits,
        for example, when you need to perform some operations after the commit
        but still within the same context.
        
        Note: After calling this method, you can continue working with the session,
        and a new transaction will be started automatically.
        """
        await self._session.commit()

    async def rollback(self) -> None:
        """
        Manually rollback the current transaction.
        
        This is useful when you need to rollback changes before the context manager exits,
        for example, when you detect a business logic error that requires rollback.
        
        Note: After calling this method, you can continue working with the session,
        and a new transaction will be started automatically.
        """
        await self._session.rollback()


# ==========================================
# Alternative: Async Context Manager Function
# ==========================================

@asynccontextmanager
async def unit_of_work():
    """
    Alternative way to use UnitOfWork as an async context manager function.
    
    This is useful when you prefer functional style over class-based approach.
    
    Usage:
        async with unit_of_work() as uow:
            user = await uow.users.upsert(user_data)
            order = await uow.orders.create(user_id=user.id, items=[...])
    
    Why provide both?
    - Class-based approach (UnitOfWork) is more explicit and easier to extend
    - Function-based approach (unit_of_work) is more Pythonic and concise
    - Both achieve the same result, so you can choose based on your preference
    """
    uow = UnitOfWork()
    async with uow:
        yield uow