from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from astroimage.config import Settings

# Test-only DSN without embedded credentials (avoids hard-coding secrets in source).
_TEST_DATABASE_URL = "postgresql+asyncpg://localhost:5432/astroimage"


def test_sync_database_url_uses_psycopg() -> None:
    settings = Settings(database_url=_TEST_DATABASE_URL)
    assert settings.sync_database_url.startswith("postgresql+psycopg://")
    assert "localhost:5432/astroimage" in settings.sync_database_url


@given(st.sampled_from(["debug", "info", "warning", "error"]))
@hypothesis_settings(max_examples=8)
def test_log_level_is_accepted(level: str) -> None:
    parsed = Settings(log_level=level, database_url=_TEST_DATABASE_URL)
    assert parsed.log_level == level


def test_database_url_is_required() -> None:
    """Settings must not ship a default password in source code."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(database_url="")
