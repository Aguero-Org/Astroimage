from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from astroimage.catalogs.cone_cache import StoredCone, StoredConeTable
from astroimage.fits.service import FitsService
from astroimage.simbad.cache import SimbadReferenceCache
from astroimage.simbad.downloads import table_from_objects
from astroimage.simbad.model import SimbadObject
from astroimage.simbad.provider import SimbadCatalogProvider
from astroimage.simbad.schema import SimbadReferencesConfigSchema
from astroimage.simbad.service import SimbadReferenceService


def _wcs_payload() -> bytes:
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [2.0, 2.0]
    wcs.wcs.crval = [10.0, 20.0]
    wcs.wcs.cdelt = [0.001, -0.001]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    buffer = BytesIO()
    fits.PrimaryHDU(np.ones((4, 4)), header=wcs.to_header()).writeto(buffer)
    return buffer.getvalue()


class _FakeFits:
    def __init__(self) -> None:
        self._payload = _wcs_payload()
        self.record_id = uuid4()
        self._record = SimpleNamespace(id=self.record_id, original_filename="image.fits")

    async def get_record(self, record_id: UUID) -> object:
        assert record_id == self.record_id
        return self._record

    async def get_payload(self, record: object) -> bytes:
        assert record is self._record
        return self._payload


class _Provider:
    def __init__(self, objects: list[SimbadObject], *, fail: bool = False) -> None:
        self._objects = objects
        self._fail = fail
        self.region_calls = 0

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
        object_type: str | None = None,
    ) -> list[SimbadObject]:
        del center, radius_arcsec, row_limit, object_type
        self.region_calls += 1
        if self._fail:
            raise RuntimeError("tap down")
        return list(self._objects)

    def query_aliases(self, main_ids: list[str], *, max_records: int) -> list[object]:
        del main_ids, max_records
        return []

    def query_references(self, main_ids: list[str], *, max_records: int) -> list[object]:
        del main_ids, max_records
        return []


class _Downloads:
    def __init__(self, *, remember: bool) -> None:
        self.found: StoredCone | None = None
        self.saves = 0
        self._remember = remember

    async def find(
        self,
        *,
        source: str,
        region_key: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        row_limit: int,
        region_suffix: str | None = None,
    ) -> StoredCone | None:
        del source, region_key, ra_deg, dec_deg, radius_arcsec, row_limit, region_suffix
        return self.found

    async def save(
        self,
        *,
        source: str,
        region_key: str,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float,
        row_limit: int,
        tables: tuple[StoredConeTable, ...],
    ) -> None:
        del source, region_key, ra_deg, dec_deg, radius_arcsec, row_limit
        self.saves += 1
        if self._remember:
            self.found = StoredCone(tables=tables, covered=False)


def _object(main_id: str) -> SimbadObject:
    return SimbadObject(main_id=main_id, ra_deg=10.0, dec_deg=20.0, separation_arcsec=0.0)


def _service(
    provider: _Provider,
    downloads: _Downloads,
    cache: SimbadReferenceCache | None = None,
) -> tuple[SimbadReferenceService, _FakeFits]:
    fits = _FakeFits()
    service = SimbadReferenceService(
        fits=cast(FitsService, fits),
        detection=None,
        provider=cast(SimbadCatalogProvider, provider),
        cache=cache or SimbadReferenceCache(),
        downloads=downloads,
    )
    return service, fits


_CONFIG = SimbadReferencesConfigSchema(include_aliases=False, include_bibliography=False)


@pytest.mark.asyncio
async def test_fresh_download_skips_the_second_tap_call() -> None:
    provider = _Provider([_object("M   1")])
    downloads = _Downloads(remember=True)
    service, fits = _service(provider, downloads)

    first = await service.references_from_record(fits.record_id, config=_CONFIG)
    second = await service.references_from_record(fits.record_id, config=_CONFIG)

    assert first.objects[0].main_id == "M   1"
    assert second.objects[0].main_id == "M   1"
    assert provider.region_calls == 1
    assert downloads.saves == 1


@pytest.mark.asyncio
async def test_memory_does_not_hide_a_different_download() -> None:
    provider = _Provider([_object("M   1")])
    downloads = _Downloads(remember=True)
    service, fits = _service(provider, downloads)
    await service.references_from_record(fits.record_id, config=_CONFIG)
    downloads.found = StoredCone(tables=(table_from_objects([_object("NGC  224")]),), covered=True)

    second = await service.references_from_record(fits.record_id, config=_CONFIG)

    assert second.objects[0].main_id == "NGC  224"
    assert provider.region_calls == 1


@pytest.mark.asyncio
async def test_store_miss_queries_simbad_again() -> None:
    provider = _Provider([_object("M   1")])
    downloads = _Downloads(remember=False)
    service, fits = _service(provider, downloads)

    await service.references_from_record(fits.record_id, config=_CONFIG)
    await service.references_from_record(fits.record_id, config=_CONFIG)

    assert provider.region_calls == 2
    assert downloads.saves == 2


@pytest.mark.asyncio
async def test_cached_tap_error_is_kept_when_nothing_is_stored() -> None:
    provider = _Provider([_object("M   1")], fail=True)
    downloads = _Downloads(remember=True)
    service, fits = _service(provider, downloads)

    first = await service.references_from_record(fits.record_id, config=_CONFIG)
    second = await service.references_from_record(fits.record_id, config=_CONFIG)

    assert first.error is not None
    assert second.error == first.error
    assert provider.region_calls == 1
    assert downloads.saves == 0
