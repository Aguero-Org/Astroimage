from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from astroimage.config import Settings, get_settings
from astroimage.shared.minio_storage import MinioObjectStorage
from astroimage.shared.object_storage import ObjectStorage


def settings_dependency() -> Settings:
    return get_settings()


async def db_session_dependency(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def minio_client_dependency(request: Request) -> Minio:
    return cast(Minio, request.app.state.minio_client)


def object_storage_dependency(
    client: Annotated[Minio, Depends(minio_client_dependency)],
    settings: Annotated[Settings, Depends(settings_dependency)],
) -> ObjectStorage:
    return MinioObjectStorage(client, settings.minio_bucket)
