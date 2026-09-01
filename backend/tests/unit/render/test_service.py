from __future__ import annotations

import io
from datetime import UTC, datetime
from uuid import uuid4

import numpy as np
import pytest
from astropy.io import fits

from astroimage.fits.model import FitsRecord
from astroimage.render.schema import RenderConfigSchema
from astroimage.render.service import RenderService

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _gradient_fits_bytes() -> bytes:
    image = np.linspace(0.0, 100.0, 64).reshape(8, 8)
    buffer = io.BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


def _gaussian_fits_bytes() -> bytes:
    rng = np.random.default_rng(seed=6)
    image = rng.normal(scale=5.0, size=(32, 32))
    buffer = io.BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


class _FakeFitsService:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._record = FitsRecord(
            id=uuid4(),
            object_key="fits/record-uuid.fits",
            original_filename="gradient.fits",
            size_bytes=len(payload),
            created_at=datetime.now(UTC),
            metadata_payload={},
        )

    async def get_record(self, record_id: object) -> FitsRecord:
        return self._record

    async def get_payload(self, record: object) -> bytes:
        return self._payload


def test_render_png_from_bytes_returns_png() -> None:
    png = RenderService().render_png_from_bytes(_gradient_fits_bytes())

    assert isinstance(png, bytes)
    assert png.startswith(_PNG_SIGNATURE)


def test_render_png_respects_custom_config() -> None:
    config = RenderConfigSchema(stretch="asinh", pmin=5.0, pmax=95.0, gamma=1.4)
    service = RenderService()

    default_png = service.render_png_from_bytes(_gradient_fits_bytes())
    custom_png = service.render_png_from_bytes(_gradient_fits_bytes(), config=config)

    assert custom_png != default_png


def test_render_png_applies_colormap() -> None:
    heat_config = RenderConfigSchema(colormap="heat")
    rainbow_config = RenderConfigSchema(colormap="rainbow")
    service = RenderService()

    grey_png = service.render_png_from_bytes(_gradient_fits_bytes())
    heat_png = service.render_png_from_bytes(_gradient_fits_bytes(), config=heat_config)
    rainbow_png = service.render_png_from_bytes(_gradient_fits_bytes(), config=rainbow_config)

    assert grey_png != heat_png
    assert heat_png != rainbow_png


def test_render_png_with_zscale_limits() -> None:
    zscale_config = RenderConfigSchema(limits="zscale", stretch="linear")
    service = RenderService()

    png = service.render_png_from_bytes(_gaussian_fits_bytes(), config=zscale_config)

    assert png.startswith(_PNG_SIGNATURE)


def test_histogram_from_bytes_reports_distribution() -> None:
    service = RenderService()

    histogram = service.histogram_from_bytes(_gaussian_fits_bytes(), bins=64)

    assert len(histogram.bin_centers) == 64
    assert len(histogram.counts) == 64
    assert sum(histogram.counts) == 32 * 32
    assert histogram.minimum <= histogram.maximum


def test_histogram_from_bytes_answers_bin_count() -> None:
    service = RenderService()

    histogram = service.histogram_from_bytes(_gaussian_fits_bytes(), bins=16)

    assert len(histogram.bin_centers) == 16
    assert sum(histogram.counts) == 32 * 32


def test_render_png_empty_payload_raises() -> None:
    with pytest.raises(ValueError, match="Empty"):
        RenderService().render_png_from_bytes(b"")


def test_render_png_garbage_payload_raises() -> None:
    with pytest.raises((ValueError, OSError)):
        RenderService().render_png_from_bytes(b"not-a-fits-file")


def test_histogram_empty_payload_raises() -> None:
    with pytest.raises(ValueError, match="Empty"):
        RenderService().histogram_from_bytes(b"")


async def test_render_png_from_record_returns_png() -> None:
    service = RenderService(fits=_FakeFitsService(_gradient_fits_bytes()))  # type: ignore[arg-type]

    png = await service.render_png_from_record(uuid4())

    assert isinstance(png, bytes)
    assert png.startswith(_PNG_SIGNATURE)


async def test_render_png_from_record_respects_custom_config() -> None:
    config = RenderConfigSchema(stretch="asinh", pmin=5.0, pmax=95.0, gamma=1.4)
    service = RenderService(fits=_FakeFitsService(_gradient_fits_bytes()))  # type: ignore[arg-type]

    default_png = await service.render_png_from_record(uuid4())
    custom_png = await service.render_png_from_record(uuid4(), config=config)

    assert custom_png != default_png


async def test_histogram_from_record_reports_distribution() -> None:
    service = RenderService(fits=_FakeFitsService(_gaussian_fits_bytes()))  # type: ignore[arg-type]

    histogram = await service.histogram_from_record(uuid4(), bins=64)

    assert len(histogram.bin_centers) == 64
    assert len(histogram.counts) == 64
    assert sum(histogram.counts) == 32 * 32
    assert histogram.minimum <= histogram.maximum


async def test_render_png_from_missing_record_raises() -> None:
    class _EmptyFitsService:
        async def get_record(self, record_id: object) -> FitsRecord:
            raise LookupError(f"FITS record not found: {record_id}")

    service = RenderService(fits=_EmptyFitsService())  # type: ignore[arg-type]

    with pytest.raises(LookupError):
        await service.render_png_from_record(uuid4())
