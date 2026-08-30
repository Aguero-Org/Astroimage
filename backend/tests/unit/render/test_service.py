from __future__ import annotations

import io

import numpy as np
import pytest
from astropy.io import fits

from astroimage.render.schema import RenderConfigSchema
from astroimage.render.service import RenderService

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _gradient_fits_bytes() -> bytes:
    image = np.linspace(0.0, 100.0, 64).reshape(8, 8)
    buffer = io.BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


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


def test_render_png_empty_payload_raises() -> None:
    with pytest.raises(ValueError, match="Empty"):
        RenderService().render_png_from_bytes(b"")


def test_render_png_garbage_payload_raises() -> None:
    with pytest.raises((ValueError, OSError)):
        RenderService().render_png_from_bytes(b"not-a-fits-file")
