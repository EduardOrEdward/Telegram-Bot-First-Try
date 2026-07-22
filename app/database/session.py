from config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    str(settings.POSTGRES_DSN),
    echo=settings.DEBUG,
    pool_pre_ping=True
)

#Factory for creating async database sessions
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    '''Dependency for getting an async database session'''
    async with async_session_factory() as session:
        yield session