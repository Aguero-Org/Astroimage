from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from astroimage.config import Settings


def test_sync_database_url_uses_psycopg() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://astroimage:astroimage@localhost:5432/astroimage"
    )
    assert settings.sync_database_url.startswith("postgresql+psycopg://")


@given(st.sampled_from(["debug", "info", "warning", "error"]))
@hypothesis_settings(max_examples=8)
def test_log_level_is_accepted(level: str) -> None:
    parsed = Settings(log_level=level)
    assert parsed.log_level == level
