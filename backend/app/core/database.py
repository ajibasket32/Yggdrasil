from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_database_session() -> AsyncIterator[AsyncSession]:
    """Yield one request-scoped database session."""
    async with session_factory() as session:
        yield session


async def dispose_database() -> None:
    """Release pooled database connections during application shutdown."""
    await engine.dispose()
