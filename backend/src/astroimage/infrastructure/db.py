from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from astroimage.config import Settings


class Base(DeclarativeBase):
    pass


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
