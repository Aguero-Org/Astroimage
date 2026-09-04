from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import numpy as np
import pytest

from astroimage.fits.model import FitsRecord
from astroimage.sources.model import ExtendedSource, PointSource, SourceDetectionResult
from astroimage.sources.schema import PointDetectionConfigSchema
from astroimage.sources.service import SourceDetectionService
from tests.unit.sources.helpers import fits_bytes_from_image, synthetic_point_source_image


class _FakeFitsService:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._record = FitsRecord(
            id=uuid4(),
            object_key="fits/record-uuid.fits",
            original_filename="survey.fits",
            size_bytes=len(payload),
            created_at=datetime.now(UTC),
            metadata_payload={},
        )

    async def get_record(self, record_id: object) -> FitsRecord:
        return self._record

    async def get_payload(self, record: object) -> bytes:
        return self._payload

    async def update_record_metadata(
        self,
        record: object,
        payload: object,
        *,
        hdu_index: object = None,
    ) -> FitsRecord:
        return self._record


def test_service_detects_point_sources_and_maps_schema() -> None:
    image, _ = synthetic_point_source_image()
    payload = fits_bytes_from_image(image)

    service = SourceDetectionService()
    config = PointDetectionConfigSchema(sigma=6.0, fwhm=5.0)
    result = service.detect(
        payload,
        source_name="survey.fits",
        config=config,
    )

    assert isinstance(result, SourceDetectionResult)
    assert result.source_name == "survey.fits"
    assert len(result.point_sources) >= 3
    assert all(isinstance(source, PointSource) for source in result.point_sources)
    ranks = [source.rank for source in result.point_sources]
    assert ranks == list(range(1, len(ranks) + 1))

    schema = service.to_schema(result)

    assert schema.source_name == result.source_name
    assert schema.summary.point_count == len(result.point_sources)
    assert schema.summary.extended_count == 0
    assert len(schema.point_sources) == len(result.point_sources)
    assert schema.point_sources[0].object_type == "point"
    assert schema.extended_sources == []


def test_service_empty_region_returns_no_sources() -> None:
    rng = np.random.default_rng(3)
    payload = fits_bytes_from_image(rng.normal(scale=5.0, size=(128, 128)))

    service = SourceDetectionService()
    result = service.detect(payload, config=PointDetectionConfigSchema(sigma=6.0))

    assert result.point_sources == []


def test_service_rejects_garbage_payload() -> None:
    service = SourceDetectionService()

    with pytest.raises(OSError):
        service.detect(b"not-a-fits-file")


async def test_detect_from_record_uses_stored_filename() -> None:
    image, _ = synthetic_point_source_image()
    payload = fits_bytes_from_image(image)
    service = SourceDetectionService(fits=_FakeFitsService(payload))  # type: ignore[arg-type]

    result = await service.detect_from_record(
        uuid4(),
        config=PointDetectionConfigSchema(sigma=6.0, fwhm=5.0),
    )

    assert result.source_name == "survey.fits"
    assert len(result.point_sources) >= 3


async def test_detect_from_missing_record_raises() -> None:
    class _EmptyFitsService:
        async def get_record(self, record_id: object) -> FitsRecord:
            raise LookupError(f"FITS record not found: {record_id}")

    service = SourceDetectionService(fits=_EmptyFitsService())  # type: ignore[arg-type]

    with pytest.raises(LookupError):
        await service.detect_from_record(uuid4())


def test_service_detects_extended_source_and_maps_schema() -> None:
    image, _ = synthetic_point_source_image(size=600)
    coordinate_y, coordinate_x = np.mgrid[0:600, 0:600]
    cosine = np.cos(np.deg2rad(45.0))
    sine = np.sin(np.deg2rad(45.0))
    delta_x = coordinate_x - 300.0
    delta_y = coordinate_y - 300.0
    axis_x = cosine * delta_x + sine * delta_y
    axis_y = -sine * delta_x + cosine * delta_y
    bivariate = (axis_x / 14.0) ** 2 + (axis_y / 3.0) ** 2
    image = image + 12000.0 * np.exp(-0.5 * bivariate)
    payload = fits_bytes_from_image(image)

    service = SourceDetectionService()
    config = PointDetectionConfigSchema(
        sigma=6.0,
        fwhm=5.0,
        extended_min_snr=100.0,
        extended_max_sources=10,
    )
    result = service.detect(payload, source_name="survey.fits", config=config)

    assert isinstance(result, SourceDetectionResult)
    extended = [source for source in result.extended_sources if isinstance(source, ExtendedSource)]
    near = [
        source
        for source in extended
        if abs(source.xcentroid - 300.0) < 8.0 and abs(source.ycentroid - 300.0) < 8.0
    ]
    assert len(near) == 1
    assert near[0].object_type == "extended"
    assert near[0].rank == 1

    schema = service.to_schema(result)
    assert schema.summary.extended_count == len(result.extended_sources)
    assert len(schema.extended_sources) == len(result.extended_sources)
    assert schema.extended_sources[0].object_type == "extended"
