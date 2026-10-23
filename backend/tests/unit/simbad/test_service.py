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

from astroimage.fits.service import FitsService
from astroimage.simbad.cache import SimbadReferenceCache
from astroimage.simbad.model import SimbadAlias, SimbadObject, SimbadReference
from astroimage.simbad.provider import SimbadCatalogProvider
from astroimage.simbad.schema import SimbadReferencesConfigSchema
from astroimage.simbad.service import SimbadReferenceService
from astroimage.sources.service import SourceDetectionService


def _wcs_payload() -> bytes:
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [2.0, 2.0]
    wcs.wcs.crval = [10.0, 20.0]
    wcs.wcs.cdelt = [0.001, -0.001]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    buffer = BytesIO()
    fits.PrimaryHDU(np.ones((4, 4)), header=wcs.to_header()).writeto(buffer)
    return buffer.getvalue()


def _plain_payload() -> bytes:
    buffer = BytesIO()
    fits.PrimaryHDU(np.ones((4, 4))).writeto(buffer)
    return buffer.getvalue()


class _FakeFits:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._record = SimpleNamespace(
            id=uuid4(),
            original_filename="image.fits",
        )

    async def get_record(self, record_id: UUID) -> object:
        assert record_id == self._record.id
        return self._record

    async def get_payload(self, record: object) -> bytes:
        assert record is self._record
        return self._payload


class _FakeProvider:
    def __init__(
        self,
        objects: list[SimbadObject] | None = None,
        aliases: list[SimbadAlias] | None = None,
        references: list[SimbadReference] | None = None,
        *,
        region_error: Exception | None = None,
        alias_error: Exception | None = None,
        reference_error: Exception | None = None,
    ) -> None:
        self._objects = objects or []
        self._aliases = aliases or []
        self._references = references or []
        self._region_error = region_error
        self._alias_error = alias_error
        self._reference_error = reference_error
        self.region_calls: list[tuple[float, float, float, int, str | None]] = []
        self.alias_calls = 0
        self.reference_calls = 0

    def query_region(
        self,
        center: SkyCoord,
        radius_arcsec: float,
        *,
        row_limit: int,
        object_type: str | None = None,
    ) -> list[SimbadObject]:
        self.region_calls.append(
            (
                float(center.ra.deg),
                float(center.dec.deg),
                radius_arcsec,
                row_limit,
                object_type,
            )
        )
        if self._region_error is not None:
            raise self._region_error
        return list(self._objects)

    def query_aliases(self, main_ids: list[str], *, max_records: int) -> list[SimbadAlias]:
        self.alias_calls += 1
        assert main_ids == ["M   1"]
        assert max_records > 0
        if self._alias_error is not None:
            raise self._alias_error
        return list(self._aliases)

    def query_references(
        self,
        main_ids: list[str],
        *,
        max_records: int,
    ) -> list[SimbadReference]:
        self.reference_calls += 1
        assert main_ids == ["M   1"]
        assert max_records > 0
        if self._reference_error is not None:
            raise self._reference_error
        return list(self._references)


class _FakeDetection:
    async def detect_from_record(
        self,
        record_id: UUID,
        *,
        client_id: str,
        hdu_index: int | None,
    ) -> object:
        assert record_id
        assert client_id == "alice"
        assert hdu_index is None
        return SimpleNamespace(
            point_sources=[SimpleNamespace(source_id=7, xcentroid=2.0, ycentroid=2.0)],
            extended_sources=[],
        )


def _object() -> SimbadObject:
    return SimbadObject(
        main_id="M   1",
        ra_deg=10.0,
        dec_deg=20.0,
        separation_arcsec=0.0,
        otype="SNR",
        otype_text="SuperNova Remnant",
        parallax_mas=1.2,
        reference_count=6602,
    )


def _service(
    provider: _FakeProvider,
    *,
    detection: SourceDetectionService | None = None,
    cache: SimbadReferenceCache | None = None,
    fits: object | None = None,
) -> SimbadReferenceService:
    return SimbadReferenceService(
        fits=cast(FitsService, fits or _FakeFits(_wcs_payload())),
        detection=detection,
        provider=cast(SimbadCatalogProvider, provider),
        cache=cache or SimbadReferenceCache(),
    )


@pytest.mark.asyncio
async def test_references_enrich_and_crossmatch_objects() -> None:
    provider = _FakeProvider(
        objects=[_object()],
        aliases=[
            SimbadAlias(object_id="M   1", name="M 1"),
            SimbadAlias(object_id="M   1", name="Gaia DR3 123456"),
        ],
        references=[
            SimbadReference(object_id="M   1", bibcode="2010A&A...1A", year=2010),
            SimbadReference(
                object_id="M   1",
                bibcode="2024A&A...2B",
                year=2024,
                doi="10.1000/example",
            ),
        ],
    )
    service = _service(
        provider,
        detection=cast(SourceDetectionService, _FakeDetection()),
    )
    result = await service.references(
        _wcs_payload(),
        record_id=uuid4(),
        client_id="alice",
        config=SimbadReferencesConfigSchema(
            max_references_per_object=1,
            crossmatch_radius_arcsec=10.0,
        ),
    )

    assert result.wcs_present is True
    assert result.queried is True
    assert result.error is None
    assert result.radius_arcsec >= 60.0
    assert result.summary.object_count == 1
    assert result.summary.detection_count == 1
    assert result.summary.matched_source_count == 1
    assert result.summary.reference_count == 1

    obj = result.objects[0]
    assert obj.main_id == "M   1"
    assert obj.gaia_source_id == "123456"
    assert obj.aliases == ["M 1", "Gaia DR3 123456"]
    assert [reference.bibcode for reference in obj.references] == ["2024A&A...2B"]
    assert obj.references[0].doi_url == "https://doi.org/10.1000/example"
    assert obj.image_match is not None
    assert obj.image_match.matched is True
    assert obj.image_match.source_id == 7
    assert provider.region_calls[0][3] == 25
    assert provider.alias_calls == 1
    assert provider.reference_calls == 1


@pytest.mark.asyncio
async def test_references_without_wcs_skips_query() -> None:
    provider = _FakeProvider(objects=[_object()])
    service = _service(provider, fits=_FakeFits(_plain_payload()))

    result = await service.references(_plain_payload())

    assert result.wcs_present is False
    assert result.queried is False
    assert result.error is None
    assert result.objects == []
    assert provider.region_calls == []


@pytest.mark.asyncio
async def test_references_surfaces_region_error() -> None:
    provider = _FakeProvider(region_error=RuntimeError("tap down"))
    result = await _service(provider).references(_wcs_payload())

    assert result.wcs_present is True
    assert result.queried is False
    assert result.error is not None
    assert "tap down" in result.error


@pytest.mark.asyncio
async def test_references_keeps_objects_when_auxiliary_queries_fail() -> None:
    provider = _FakeProvider(
        objects=[_object()],
        alias_error=RuntimeError("ident down"),
        reference_error=RuntimeError("ref down"),
    )
    result = await _service(provider).references(_wcs_payload())

    assert result.queried is True
    assert len(result.objects) == 1
    assert result.objects[0].aliases == []
    assert result.objects[0].references == []
    assert len(result.warnings) == 2
    assert any("ident down" in warning for warning in result.warnings)
    assert any("ref down" in warning for warning in result.warnings)


@pytest.mark.asyncio
async def test_references_skips_bibliography_when_disabled() -> None:
    provider = _FakeProvider(objects=[_object()])
    result = await _service(provider).references(
        _wcs_payload(),
        config=SimbadReferencesConfigSchema(include_bibliography=False),
    )

    assert result.queried is True
    assert result.objects[0].references == []
    assert provider.reference_calls == 0


@pytest.mark.asyncio
async def test_references_from_record_caches_until_refresh() -> None:
    fake_fits = _FakeFits(_wcs_payload())
    provider = _FakeProvider(objects=[_object()])
    cache = SimbadReferenceCache()
    service = _service(provider, fits=fake_fits, cache=cache)
    record_id = cast(UUID, fake_fits._record.id)

    first = await service.references_from_record(record_id, client_id="alice")
    second = await service.references_from_record(record_id, client_id="alice")
    refreshed = await service.references_from_record(
        record_id,
        client_id="alice",
        refresh=True,
    )

    assert first == second
    assert refreshed == first
    assert len(provider.region_calls) == 2
