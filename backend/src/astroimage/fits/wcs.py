from __future__ import annotations

import warnings

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning

from astroimage.fits.reader import FitsMetadata


def world_coordinates(metadata: FitsMetadata) -> WCS | None:
    if not metadata.wcs.present:
        return None
    header = fits.Header()
    for key, value in metadata.header.items():
        header[key] = value
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FITSFixedWarning)
        return WCS(header, naxis=2, relax=True)


def field_center(wcs: WCS) -> SkyCoord:
    crval = wcs.wcs.crval
    return SkyCoord(ra=float(crval[0]) * u.deg, dec=float(crval[1]) * u.deg, frame="icrs")


def to_sky(wcs: WCS, x: float, y: float) -> SkyCoord:
    world = wcs.pixel_to_world(x, y)
    return SkyCoord(ra=float(world.ra.deg) * u.deg, dec=float(world.dec.deg) * u.deg, frame="icrs")
