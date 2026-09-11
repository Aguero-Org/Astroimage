from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from astroimage.fits.model import FitsRecord
from astroimage.fits.reader import FitsHduInfo, FitsMetadata
from astroimage.fits.service import FitsService


class _FakeReader:
    def read_metadata_from_bytes(
        self,
        payload: bytes,
        *,
        source_name: str,
        hdu_index: int | None = None,
    ) -> FitsMetadata:
        return FitsMetadata(
            source_name=source_name,
            header={"OBJ": "TEST", "AI_SRC": "hubble-mast"},
            hdus=FitsHduInfo(selected=0, image_indices=[0]),
        )

    def source_filename_from_bytes(self, payload: bytes) -> str | None:
        return None


class _FakeStorage:
    def __init__(self) -> None:
        self.uploaded: list[tuple[str, bytes]] = []
        self.payloads: dict[str, bytes] = {}
        self.fail_put = False

    def object_key_for(self, record_id: UUID, source_name: str) -> str:
        return f"fits/{record_id}.fits"

    async def put_at(self, object_key: str, payload: bytes) -> None:
        if self.fail_put:
            raise RuntimeError("storage unavailable")
        self.uploaded.append((object_key, payload))
        self.payloads[object_key] = payload

    async def get(self, object_key: str) -> bytes:
        return self.payloads[object_key]

    async def list_fits_keys(self) -> list[str]:
        return sorted(self.payloads)


class _FakeRepository:
    def __init__(self) -> None:
        self.created: list[FitsRecord] = []
        self.deleted: list[UUID] = []
        self.updated: list[FitsRecord] = []
        self.rows: dict[UUID, FitsRecord] = {}

    async def create(self, record: FitsRecord) -> FitsRecord:
        self.created.append(record)
        self.rows[record.id] = record
        return record

    async def get(self, record_id: UUID) -> FitsRecord:
        record = self.rows.get(record_id)
        if record is None:
            raise LookupError(f"FITS record not found: {record_id}")
        return record

    async def update(self, record: FitsRecord) -> FitsRecord:
        self.updated.append(record)
        return record

    async def delete(self, record: FitsRecord) -> None:
        self.deleted.append(record.id)


def _service(
    storage: _FakeStorage,
    repository: _FakeRepository,
    reader: _FakeReader | None = None,
) -> FitsService:
    return FitsService(reader or _FakeReader(), repository, storage)  # type: ignore[arg-type]


async def test_store_bytes_persists_metadata_then_uploads_object() -> None:
    storage = _FakeStorage()
    repository = _FakeRepository()
    service = _service(storage, repository)

    record = await service.store_bytes(b"payload", source_name="hst_drz.fits")

    assert len(repository.created) == 1
    assert repository.created[0] is record
    assert record.object_key == f"fits/{record.id}.fits"
    assert record.metadata_payload["header"]["AI_SRC"] == "hubble-mast"
    assert storage.uploaded == [(f"fits/{record.id}.fits", b"payload")]


async def test_store_bytes_without_analysis_skips_metadata_read() -> None:
    storage = _FakeStorage()
    repository = _FakeRepository()
    service = _service(storage, repository)

    record = await service.store_bytes(
        b"payload",
        source_name="hst_drz.fits",
        analyze=False,
    )

    assert record.metadata_payload == {
        "source_name": "hst_drz.fits",
        "hdus": {"selected": 0},
    }
    assert storage.uploaded == [(f"fits/{record.id}.fits", b"payload")]


async def test_update_record_metadata_persists_analyzed_payload() -> None:
    storage = _FakeStorage()
    repository = _FakeRepository()
    service = _service(storage, repository)
    record = FitsRecord(
        id=uuid4(),
        object_key=f"fits/{uuid4()}.fits",
        original_filename="hst_drz.fits",
        size_bytes=7,
        metadata_payload={"source_name": "hst_drz.fits", "hdus": {"selected": 0}},
    )

    updated = await service.update_record_metadata(record, b"payload")

    assert updated is record
    assert repository.updated == [record]
    assert record.metadata_payload["header"]["AI_SRC"] == "hubble-mast"
    assert record.metadata_payload["hdus"]["selected"] == 0
    assert record.metadata_payload["hdus"]["image_indices"] == [0]
    assert record.metadata_payload["hdus"]["images"] == []


async def test_store_bytes_rolls_back_record_when_upload_fails() -> None:
    storage = _FakeStorage()
    storage.fail_put = True
    repository = _FakeRepository()
    service = _service(storage, repository)

    with pytest.raises(RuntimeError, match="storage unavailable"):
        await service.store_bytes(b"payload", source_name="hst_drz.fits")

    assert len(repository.created) == 1
    assert repository.deleted == [repository.created[0].id]
    assert storage.uploaded == []


async def test_store_bytes_generates_distinct_object_ids() -> None:
    storage = _FakeStorage()
    service = _service(storage, _FakeRepository())

    first = await service.store_bytes(b"payload", source_name="a.fits")
    second = await service.store_bytes(b"payload", source_name="b.fits")

    assert first.id != second.id
    assert first.object_key != second.object_key
    assert str(first.id) != str(uuid4())


async def test_reconcile_records_creates_rows_for_orphaned_objects() -> None:
    first_id = uuid4()
    second_id = uuid4()
    storage = _FakeStorage()
    storage.payloads = {
        f"fits/{first_id}.fits": b"payload-a",
        f"fits/{second_id}.fits": b"payload-b",
    }
    repository = _FakeRepository()
    service = _service(storage, repository)

    report = await service.reconcile_records()

    assert report.failed == []
    assert len(report.created) == 2
    assert {record.id for record in repository.created} == {first_id, second_id}
    for record in repository.created:
        assert record.object_key == f"fits/{record.id}.fits"
        assert record.original_filename == f"{record.id}.fits"
        assert record.size_bytes == len(b"payload-x")
        assert record.metadata_payload["hdus"]["selected"] == 0


async def test_reconcile_records_skips_existing_records() -> None:
    existing_id = uuid4()
    storage = _FakeStorage()
    storage.payloads = {f"fits/{existing_id}.fits": b"payload"}
    repository = _FakeRepository()
    repository.rows[existing_id] = FitsRecord(
        id=existing_id,
        object_key=f"fits/{existing_id}.fits",
        original_filename="existing.fits",
        size_bytes=7,
        metadata_payload={"source_name": "existing.fits", "hdus": {"selected": 0}},
    )
    service = _service(storage, repository)

    report = await service.reconcile_records()

    assert report.created == []
    assert report.skipped == [f"fits/{existing_id}.fits"]
    assert repository.created == []


async def test_reconcile_records_updates_fallback_name() -> None:
    existing_id = uuid4()
    storage = _FakeStorage()
    storage.payloads = {f"fits/{existing_id}.fits": b"payload"}
    repository = _FakeRepository()
    existing = FitsRecord(
        id=existing_id,
        object_key=f"fits/{existing_id}.fits",
        original_filename=f"{existing_id}.fits",
        size_bytes=7,
        metadata_payload={"source_name": f"{existing_id}.fits", "hdus": {"selected": 0}},
    )
    repository.rows[existing_id] = existing

    class _NamedReader(_FakeReader):
        def source_filename_from_bytes(self, payload: bytes) -> str | None:
            return "hst_10118_02_acs_wfc_fr423n_flc.fits"

    service = _service(storage, repository, reader=_NamedReader())

    report = await service.reconcile_records()

    assert report.created == []
    assert report.skipped == []
    assert report.updated == [f"fits/{existing_id}.fits"]
    assert existing.original_filename == "hst_10118_02_acs_wfc_fr423n_flc.fits"
    assert repository.updated == [existing]
