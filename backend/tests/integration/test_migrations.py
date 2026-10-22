from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

from astroimage.catalogs.download import CatalogDownload
from astroimage.config import get_settings
from astroimage.fits.model import FitsRecord
from astroimage.hub.model import ImageTransfer
from astroimage.shared.database import Base

_MODELS = (CatalogDownload, FitsRecord, ImageTransfer)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DATABASE_NAME = "astroimage_migrations"


def _admin_url(sync_database_url: str) -> str:
    return sync_database_url.rsplit("/", 1)[0] + "/postgres"


def _database_url(database_url: str) -> str:
    return database_url.rsplit("/", 1)[0] + f"/{_DATABASE_NAME}"


def _drop_database(admin_url: str) -> None:
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{_DATABASE_NAME}" WITH (FORCE)'))
    finally:
        engine.dispose()


def _create_database(admin_url: str) -> None:
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{_DATABASE_NAME}"'))
    finally:
        engine.dispose()


def test_migrations_match_orm_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    admin_url = _admin_url(settings.sync_database_url)
    migration_database_url = _database_url(settings.database_url)
    migration_sync_url = _database_url(settings.sync_database_url)
    previous_database_url = os.environ.get("DATABASE_URL")

    _drop_database(admin_url)
    _create_database(admin_url)
    monkeypatch.setenv("DATABASE_URL", migration_database_url)
    get_settings.cache_clear()
    try:
        config = Config(str(_BACKEND_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
        command.upgrade(config, "head")

        engine = create_engine(migration_sync_url)
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                diff = compare_metadata(context, Base.metadata)
        finally:
            engine.dispose()
    finally:
        get_settings.cache_clear()
        _drop_database(admin_url)
        if previous_database_url is None:
            monkeypatch.delenv("DATABASE_URL", raising=False)
        else:
            monkeypatch.setenv("DATABASE_URL", previous_database_url)

    assert diff == []
