from __future__ import annotations

import numpy as np
import pytest

from astroimage.sources.model import PointSource, SourceDetectionResult
from astroimage.sources.schema import PointDetectionConfigSchema
from astroimage.sources.service import SourceDetectionService
from tests.unit.sources.helpers import fits_bytes_from_image, synthetic_point_source_image


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
