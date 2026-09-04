from __future__ import annotations

import getpass
import io
import json
import tarfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_RECORDS_MEMBER = "records.json"
_MANIFEST_MEMBER = "manifest.json"
_OBJECTS_PREFIX = "objects/"
_SNAPSHOT_SUFFIX = ".tar.gz"


@dataclass(frozen=True)
class SnapshotManifest:
    name: str
    created_at: str
    created_by: str
    record_count: int


def default_snapshot_stem(when: datetime | None = None) -> str:
    stamp = (when or datetime.now(UTC)).strftime("%Y-%m-%d-%H%M%SZ")
    return f"seed-{stamp}"


def build_manifest(*, name: str, record_count: int) -> SnapshotManifest:
    return SnapshotManifest(
        name=name,
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        created_by=getpass.getuser(),
        record_count=record_count,
    )


def snapshot_path(path: str | Path) -> Path:
    resolved = Path(path)
    name = resolved.name.lower()
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        return resolved
    return resolved.with_name(resolved.name + _SNAPSHOT_SUFFIX)


def pack_snapshot(
    records: Sequence[Mapping[str, object]],
    objects: Mapping[str, bytes],
    *,
    manifest: SnapshotManifest,
) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        manifest_bytes = json.dumps(
            {
                "name": manifest.name,
                "created_at": manifest.created_at,
                "created_by": manifest.created_by,
                "record_count": manifest.record_count,
            },
            indent=2,
        ).encode("utf-8")
        _add_bytes(archive, _MANIFEST_MEMBER, manifest_bytes)
        records_bytes = json.dumps(list(records), indent=2).encode("utf-8")
        _add_bytes(archive, _RECORDS_MEMBER, records_bytes)
        for object_key, payload in objects.items():
            _add_bytes(archive, f"{_OBJECTS_PREFIX}{object_key}", payload)
    return buffer.getvalue()


def unpack_snapshot(
    payload: bytes,
) -> tuple[list[dict[str, object]], dict[str, bytes], SnapshotManifest | None]:
    buffer = io.BytesIO(payload)
    records: list[dict[str, object]] = []
    objects: dict[str, bytes] = {}
    manifest: SnapshotManifest | None = None
    with tarfile.open(fileobj=buffer, mode="r:gz") as archive:
        for member in archive.getmembers():
            content = _read_safe_member(archive, member)
            if content is None:
                continue
            records, objects, manifest = _ingest_member(
                member.name, content, records, objects, manifest
            )
    return records, objects, manifest


def _is_safe_tar_name(name: str) -> bool:
    path = Path(name)
    if path.is_absolute() or bool(path.anchor):
        return False
    return ".." not in path.parts


def _read_safe_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes | None:
    if not member.isfile() or not _is_safe_tar_name(member.name):
        return None
    extracted = archive.extractfile(member)
    if extracted is None:
        return None
    return extracted.read()


def _ingest_member(
    name: str,
    content: bytes,
    records: list[dict[str, object]],
    objects: dict[str, bytes],
    manifest: SnapshotManifest | None,
) -> tuple[list[dict[str, object]], dict[str, bytes], SnapshotManifest | None]:
    if name == _MANIFEST_MEMBER:
        parsed = json.loads(content.decode("utf-8"))
        if isinstance(parsed, dict):
            return records, objects, _manifest_from_dict(parsed)
        return records, objects, manifest
    if name == _RECORDS_MEMBER:
        parsed = json.loads(content.decode("utf-8"))
        if isinstance(parsed, list):
            records = [item for item in parsed if isinstance(item, dict)]
        return records, objects, manifest
    if name.startswith(_OBJECTS_PREFIX):
        objects[name.removeprefix(_OBJECTS_PREFIX)] = content
    return records, objects, manifest


def _manifest_from_dict(raw: dict[str, object]) -> SnapshotManifest:
    record_count = raw.get("record_count")
    return SnapshotManifest(
        name=str(raw.get("name") or ""),
        created_at=str(raw.get("created_at") or ""),
        created_by=str(raw.get("created_by") or ""),
        record_count=record_count if isinstance(record_count, int) else 0,
    )


def _add_bytes(archive: tarfile.TarFile, name: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(payload)
    archive.addfile(info, io.BytesIO(payload))
