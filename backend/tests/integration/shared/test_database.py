import pytest
from sqlalchemy import text

from astroimage.config import Settings
from astroimage.shared.database import create_engine_from_settings, create_session_factory


@pytest.mark.asyncio
async def test_engine_and_session_query_postgres(settings: Settings) -> None:
    engine = create_engine_from_settings(settings)
    factory = create_session_factory(engine)
    try:
        async with factory() as session:
            value = await session.scalar(text("SELECT 1"))
        assert value == 1
    finally:
        await engine.dispose()
