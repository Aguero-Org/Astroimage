from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from astroimage.scripts.paths import backend_root

if TYPE_CHECKING:
    from alembic.config import Config


def _alembic_config() -> Config:
    from alembic.config import Config

    root = backend_root()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    return config


def cmd_db_upgrade(args: argparse.Namespace) -> int:
    from alembic import command

    command.upgrade(_alembic_config(), args.revision)
    return 0


def cmd_db_revision(args: argparse.Namespace) -> int:
    from alembic import command

    command.revision(
        _alembic_config(),
        message=args.message,
        autogenerate=args.autogenerate,
    )
    return 0


def cmd_db_reconcile(_args: argparse.Namespace) -> int:
    import asyncio

    from astroimage.config import get_settings
    from astroimage.fits.reader import FitsReader
    from astroimage.fits.repository import FitsRepository
    from astroimage.fits.service import FitsService, ReconcileReport
    from astroimage.fits.storage import FitsStorage
    from astroimage.shared.database import (
        create_engine_from_settings,
        create_session_factory,
    )
    from astroimage.shared.minio_storage import (
        MinioObjectStorage,
        create_object_storage_client,
    )

    async def _run() -> ReconcileReport:
        settings = get_settings()
        engine = create_engine_from_settings(settings)
        session_factory = create_session_factory(engine)
        client = create_object_storage_client(settings)
        objects = MinioObjectStorage(client, settings.minio_bucket)
        storage = FitsStorage(objects)
        try:
            async with session_factory() as session:
                repository = FitsRepository(session)
                service = FitsService(FitsReader(), repository, storage)
                report = await service.reconcile_records()
                await session.commit()
                return report
        finally:
            await engine.dispose()

    report = asyncio.run(_run())
    print(
        f"reconcile: created={len(report.created)} "
        f"updated={len(report.updated)} skipped={len(report.skipped)} "
        f"failed={len(report.failed)}"
    )
    for key in report.created:
        print(f"  created: {key}")
    for key in report.updated:
        print(f"  updated: {key}")
    for key in report.failed:
        print(f"  failed:  {key}")
    return 1 if report.failed else 0
