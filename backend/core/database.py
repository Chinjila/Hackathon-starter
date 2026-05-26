"""Database Configuration - Async SQLAlchemy setup for PostgreSQL"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from backend.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True if settings.ENVIRONMENT == "development" else False,
    future=True
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# Base class for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


# Dependency for FastAPI endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields database sessions and owns transaction finalization.
    
    Usage in FastAPI endpoints:
        @router.get("/")
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass

    Successful requests are committed here after the endpoint returns.
    If any exception bubbles up, the session is rolled back here.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()