import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://anonshare:anonshare@localhost:5432/anonshare",
)

# Railway provides postgresql:// — async SQLAlchemy needs asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)


class Base(DeclarativeBase):
    pass


def create_engine(url: str = DATABASE_URL, *, echo: bool | None = None) -> AsyncEngine:
    if echo is None:
        echo = os.getenv("SQL_ECHO", "").lower() in ("1", "true", "yes")
    return create_async_engine(
        url,
        echo=echo,
        pool_pre_ping=True,
    )


engine: AsyncEngine = create_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Backward-compatible alias used elsewhere in the project
async_session = async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (dev convenience; use Alembic in production)."""
    import models  # noqa: F401 — register ORM tables on Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
