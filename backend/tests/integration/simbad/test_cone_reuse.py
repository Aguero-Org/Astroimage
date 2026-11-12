from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.catalogs.cone_cache import CatalogConeCache
from astroimage.catalogs.download import CatalogDownload
from astroimage.catalogs.repository import CatalogDownloadRepository
from astroimage.fits.service import FitsService
from astroimage.simbad.cache import SimbadReferenceCache
from astroimage.simbad.downloads import simbad_download_query, table_from_objects
from astroimage.simbad.model import SimbadObject
from astroimage.simbad.provider import SimbadCatalogProvider
from astroimage.simbad.schema import SimbadReferencesConfigSchema
from astroimage.simbad.service import SimbadReferenceService

_CONFIG = SimbadReferencesConfigSchema(
    limit=2,
    include_aliases=False,
    include_bibliography=False,
)


def _payload() -> bytes:
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [2.0, 2.0]
    wcs.wcs.crval = [10.0, 20.0]
    wcs.wcs.cdelt = [0.001, -0.001]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    buffer = BytesIO()
    fits.PrimaryHDU(np.ones((4, 4)), header=wcs.to_header()).writeto(buffer)
    return buffer.getvalue()


class _Fits:
    def __init__(self) -> None:
        self._payload = _payload()
        self.record_id = uuid4()
        self._record = SimpleNamespace(id=self.record_id, original_filename="image.fits")

    async def get_record(self, record_id: UUID) -> object:
        assert record_id == self.record_id
        return self._record

    async def get_payload(self, record: object) -> bytes:
        return self._payload


class _Provider:
    def __init__(self, main_id: str = "M   1") -> None:
        self._main_id = main_id
        self.calls: list[tuple[float, float, float, int, str | None]] = []

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
        object_type: str | None = None,
    ) -> list[SimbadObject]:
        self.calls.append(
            (
                float(center.ra.deg),
                float(center.dec.deg),
                radius_arcsec,
                row_limit,
                object_type,
            )
        )
        return [_object(self._main_id, float(center.ra.deg), float(center.dec.deg))]

    def query_aliases(self, main_ids: list[str], *, max_records: int) -> list[object]:
        del main_ids, max_records
        return []

    def query_references(self, main_ids: list[str], *, max_records: int) -> list[object]:
        del main_ids, max_records
        return []


def _object(main_id: str, ra_deg: float = 10.0, dec_deg: float = 20.0) -> SimbadObject:
    return SimbadObject(
        main_id=main_id,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        separation_arcsec=0.0,
        otype="SNR",
    )


def _stack(
    session: AsyncSession,
    provider: _Provider,
) -> tuple[SimbadReferenceService, CatalogConeCache, _Fits]:
    fits = _Fits()
    downloads = CatalogConeCache(CatalogDownloadRepository(session, ttl_s=3600))
    service = SimbadReferenceService(
        fits=cast(FitsService, fits),
        detection=None,
        provider=cast(SimbadCatalogProvider, provider),
        cache=SimbadReferenceCache(),
        downloads=downloads,
    )
    return service, downloads, fits


async def _clear(session: AsyncSession) -> None:
    await session.execute(delete(CatalogDownload))
    await session.flush()


async def test_covered_cone_skips_simbad(db_session: AsyncSession) -> None:
    provider = _Provider()
    service, downloads, fits = _stack(db_session, provider)
    await service.references_from_record(fits.record_id, config=_CONFIG)
    ra_deg, dec_deg, radius_arcsec, row_limit, object_type = provider.calls[0]
    await _clear(db_session)
    query = simbad_download_query(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        radius_arcsec=radius_arcsec + 100,
        row_limit=row_limit,
        object_type=object_type,
    )
    await downloads.save(
        source=query.source,
        region_key=query.region_key,
        ra_deg=query.ra_deg,
        dec_deg=query.dec_deg,
        radius_arcsec=query.radius_arcsec,
        row_limit=query.row_limit,
        tables=(table_from_objects([_object("NGC  224", ra_deg, dec_deg)]),),
    )

    result = await service.references_from_record(fits.record_id, config=_CONFIG)

    assert result.objects[0].main_id == "NGC  224"
    assert len(provider.calls) == 1


async def test_cone_outside_every_download_queries_simbad(db_session: AsyncSession) -> None:
    provider = _Provider()
    service, downloads, fits = _stack(db_session, provider)
    query = simbad_download_query(
        ra_deg=0.0,
        dec_deg=0.0,
        radius_arcsec=10.0,
        row_limit=_CONFIG.limit,
        object_type=None,
    )
    await downloads.save(
        source=query.source,
        region_key=query.region_key,
        ra_deg=query.ra_deg,
        dec_deg=query.dec_deg,
        radius_arcsec=query.radius_arcsec,
        row_limit=query.row_limit,
        tables=(table_from_objects([_object("NGC  224", 0.0, 0.0)]),),
    )

    result = await service.references_from_record(fits.record_id, config=_CONFIG)

    assert result.objects[0].main_id == "M   1"
    assert len(provider.calls) == 1


async def test_truncated_download_does_not_cover_another_cone(db_session: AsyncSession) -> None:
    provider = _Provider()
    service, downloads, fits = _stack(db_session, provider)
    await service.references_from_record(fits.record_id, config=_CONFIG)
    ra_deg, dec_deg, radius_arcsec, row_limit, object_type = provider.calls[0]
    await _clear(db_session)
    query = simbad_download_query(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        radius_arcsec=radius_arcsec + 100,
        row_limit=row_limit,
        object_type=object_type,
    )
    await downloads.save(
        source=query.source,
        region_key=query.region_key,
        ra_deg=query.ra_deg,
        dec_deg=query.dec_deg,
        radius_arcsec=query.radius_arcsec,
        row_limit=query.row_limit,
        tables=(
            table_from_objects(
                [
                    _object("NGC  224", ra_deg, dec_deg),
                    _object("NGC  225", ra_deg, dec_deg),
                ]
            ),
        ),
    )

    result = await service.references_from_record(fits.record_id, config=_CONFIG)

    assert result.objects[0].main_id == "M   1"
    assert len(provider.calls) == 2


async def test_exact_truncated_download_is_reused(db_session: AsyncSession) -> None:
    provider = _Provider()
    service, downloads, fits = _stack(db_session, provider)
    filled = SimbadReferencesConfigSchema(
        limit=1,
        include_aliases=False,
        include_bibliography=False,
    )
    await service.references_from_record(fits.record_id, config=filled)
    ra_deg, dec_deg, radius_arcsec, row_limit, object_type = provider.calls[0]
    await _clear(db_session)
    query = simbad_download_query(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        radius_arcsec=radius_arcsec,
        row_limit=row_limit,
        object_type=object_type,
    )
    await downloads.save(
        source=query.source,
        region_key=query.region_key,
        ra_deg=query.ra_deg,
        dec_deg=query.dec_deg,
        radius_arcsec=query.radius_arcsec,
        row_limit=query.row_limit,
        tables=(table_from_objects([_object("NGC  224", ra_deg, dec_deg)]),),
    )

    result = await service.references_from_record(fits.record_id, config=filled)

    assert result.objects[0].main_id == "NGC  224"
    assert len(provider.calls) == 1
