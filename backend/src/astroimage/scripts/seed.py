from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from astroimage.scripts.github_releases import GitHubReleaseCatalog

if TYPE_CHECKING:
    from astroimage.fits.model import FitsRecord


def _seed_catalog(args: argparse.Namespace) -> GitHubReleaseCatalog:
    return GitHubReleaseCatalog(owner=args.owner, repo=args.repo)


def _require_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("expected int")
    return value


def _require_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError("expected object")
    return value


def _record_to_snapshot(record: FitsRecord) -> dict[str, object]:
    return {
        "id": str(record.id),
        "object_key": record.object_key,
        "original_filename": record.original_filename,
        "size_bytes": record.size_bytes,
        "metadata_payload": record.metadata_payload,
    }


def cmd_seed_dump(args: argparse.Namespace) -> int:
    import asyncio

    from astroimage.config import get_settings
    from astroimage.fits.repository import FitsRepository
    from astroimage.fits.storage import FitsStorage
    from astroimage.scripts.snapshot import (
        build_manifest,
        default_snapshot_stem,
        pack_snapshot,
        snapshot_path,
    )
    from astroimage.shared.database import (
        create_engine_from_settings,
        create_session_factory,
    )
    from astroimage.shared.minio_storage import (
        MinioObjectStorage,
        create_object_storage_client,
    )

    async def _run() -> bytes:
        settings = get_settings()
        engine = create_engine_from_settings(settings)
        session_factory = create_session_factory(engine)
        client = create_object_storage_client(settings)
        storage = FitsStorage(MinioObjectStorage(client, settings.minio_bucket))
        records: list[dict[str, object]] = []
        objects: dict[str, bytes] = {}
        try:
            async with session_factory() as session:
                repository = FitsRepository(session)
                offset = 0
                page_size = 100
                while True:
                    batch = await repository.list(offset=offset, limit=page_size)
                    if not batch:
                        break
                    for record in batch:
                        records.append(_record_to_snapshot(record))
                        objects[record.object_key] = await storage.get(record.object_key)
                    offset += page_size
        finally:
            await engine.dispose()
        stem = Path(args.output).name if args.output else default_snapshot_stem()
        manifest = build_manifest(name=stem, record_count=len(records))
        return pack_snapshot(records, objects, manifest=manifest)

    archive = asyncio.run(_run())
    output_arg = args.output if args.output else default_snapshot_stem()
    output = snapshot_path(output_arg)
    output.write_bytes(archive)
    print(f"wrote {output} ({len(archive)} bytes)")
    if args.tag:
        catalog = _seed_catalog(args)
        catalog.ensure_release(args.tag)
        catalog.upload_file(args.tag, output)
        print(f"uploaded {output.name} to release {args.tag}")
    return 0


def cmd_seed_load(args: argparse.Namespace) -> int:
    import asyncio
    from uuid import UUID

    from astroimage.config import get_settings
    from astroimage.fits.model import FitsRecord
    from astroimage.fits.repository import FitsRepository
    from astroimage.fits.storage import FitsStorage
    from astroimage.scripts.snapshot import snapshot_path, unpack_snapshot
    from astroimage.shared.database import (
        create_engine_from_settings,
        create_session_factory,
    )
    from astroimage.shared.minio_storage import (
        MinioObjectStorage,
        create_object_storage_client,
    )

    if args.file:
        archive = snapshot_path(args.file).read_bytes()
    elif args.tag:
        archive = _seed_catalog(args).download_snapshot(args.tag)
    else:
        raise SystemExit("seed load requires --file or --tag")

    records, objects, manifest = unpack_snapshot(archive)
    if manifest is not None:
        print(
            f"snapshot {manifest.name} by {manifest.created_by} "
            f"at {manifest.created_at} records={manifest.record_count}"
        )

    async def _run() -> tuple[int, int]:
        settings = get_settings()
        engine = create_engine_from_settings(settings)
        session_factory = create_session_factory(engine)
        client = create_object_storage_client(settings)
        storage = FitsStorage(MinioObjectStorage(client, settings.minio_bucket))
        restored = 0
        skipped = 0
        try:
            async with session_factory() as session:
                repository = FitsRepository(session)
                for row in records:
                    record_id = UUID(str(row["id"]))
                    object_key = str(row["object_key"])
                    try:
                        await repository.get(record_id)
                    except LookupError:
                        pass
                    else:
                        skipped += 1
                        continue
                    payload = objects.get(object_key)
                    if payload is None:
                        skipped += 1
                        continue
                    await storage.put_at(object_key, payload)
                    await repository.create(
                        FitsRecord(
                            id=record_id,
                            object_key=object_key,
                            original_filename=str(row["original_filename"]),
                            size_bytes=_require_int(row["size_bytes"]),
                            metadata_payload=_require_dict(row["metadata_payload"]),
                        )
                    )
                    restored += 1
                await session.commit()
        finally:
            await engine.dispose()
        return restored, skipped

    restored, skipped = asyncio.run(_run())
    print(f"seed load: restored={restored} skipped={skipped}")
    return 0


def cmd_seed_list(args: argparse.Namespace) -> int:
    from astroimage.scripts.snapshot import snapshot_path, unpack_snapshot

    if args.file:
        archive = snapshot_path(args.file).read_bytes()
        _records, _objects, manifest = unpack_snapshot(archive)
        if manifest is None:
            print("no manifest in snapshot")
            return 1
        print(
            f"{manifest.name}\t{manifest.created_by}\t{manifest.created_at}\t"
            f"records={manifest.record_count}"
        )
        return 0
    if args.tag:
        assets = _seed_catalog(args).list_assets(args.tag)
        if not assets:
            print(f"no assets on release {args.tag}")
            return 1
        for asset in assets:
            print(
                f"{asset.name}\t{asset.uploaded_by or '-'}\t"
                f"{asset.updated_at or '-'}\t{asset.size_bytes}B"
            )
        return 0
    raise SystemExit("seed list requires --file or --tag")


def cmd_seed_delete(args: argparse.Namespace) -> int:
    from astroimage.scripts.snapshot import snapshot_path

    if args.file:
        path = snapshot_path(args.file)
        if not path.is_file():
            print(f"not found {path}")
            return 1
        path.unlink()
        print(f"deleted {path}")
        return 0
    if not args.tag:
        raise SystemExit("seed delete requires --file or --tag")
    catalog = _seed_catalog(args)
    assets = catalog.list_assets(args.tag)
    snapshots = [
        asset
        for asset in assets
        if asset.name.lower().endswith(".tar.gz") or asset.name.lower().endswith(".tgz")
    ]
    if args.name:
        wanted = snapshot_path(args.name).name
        snapshots = [asset for asset in snapshots if asset.name in {wanted, args.name}]
    if len(snapshots) != 1:
        raise SystemExit("seed delete --tag needs --name with the snapshot filename")
    target = snapshots[0]
    catalog.delete_asset(args.tag, target.name)
    print(f"deleted {target.name} from release {args.tag}")
    return 0
