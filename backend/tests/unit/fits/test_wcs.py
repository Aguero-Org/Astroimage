from __future__ import annotations

import pytest

from astroimage.fits.reader import FitsHduInfo, FitsMetadata, FitsWcsInfo
from astroimage.fits.wcs import field_center, to_sky, world_coordinates

_HEADER = {
    "CRVAL1": 150.0,
    "CRVAL2": 2.0,
    "CRPIX1": 1.0,
    "CRPIX2": 1.0,
    "CTYPE1": "RA---TAN",
    "CTYPE2": "DEC--TAN",
    "CD1_1": -0.001,
    "CD1_2": 0.0,
    "CD2_1": 0.0,
    "CD2_2": 0.001,
}


def _metadata(*, present: bool = True) -> FitsMetadata:
    return FitsMetadata(
        hdus=FitsHduInfo(selected=0),
        wcs=FitsWcsInfo(present=present),
        header=_HEADER,
    )


def test_world_coordinates_returns_none_without_wcs() -> None:
    assert world_coordinates(_metadata(present=False)) is None


def test_to_sky_maps_the_reference_pixel_to_crval() -> None:
    wcs = world_coordinates(_metadata())
    assert wcs is not None

    coordinate = to_sky(wcs, 0.0, 0.0)

    assert coordinate.ra.deg == pytest.approx(150.0)
    assert coordinate.dec.deg == pytest.approx(2.0)


def test_to_sky_uses_the_header_scale() -> None:
    wcs = world_coordinates(_metadata())
    assert wcs is not None

    coordinate = to_sky(wcs, 1.0, 0.0)

    assert coordinate.ra.deg == pytest.approx(149.999)
    assert coordinate.dec.deg == pytest.approx(2.0)


def test_field_center_uses_crval() -> None:
    wcs = world_coordinates(_metadata())
    assert wcs is not None

    center = field_center(wcs)

    assert center.ra.deg == pytest.approx(150.0)
    assert center.dec.deg == pytest.approx(2.0)
