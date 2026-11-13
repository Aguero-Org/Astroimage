from __future__ import annotations

import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table

from astroimage.sources.gaia import (
    FallbackGaiaProvider,
    GaiaObject,
    GaiaQueryError,
    _vizier_gaia_objects,
)

_CENTER = SkyCoord(ra=10.7 * u.deg, dec=41.27 * u.deg, frame="icrs")


class _FailingProvider:
    def __init__(self, message: str) -> None:
        self._message = message

    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]:
        raise GaiaQueryError(self._message)


class _StaticProvider:
    def __init__(self, objects: list[GaiaObject]) -> None:
        self._objects = objects
        self.calls = 0

    def search_cone(self, center: SkyCoord, radius_arcsec: float) -> list[GaiaObject]:
        self.calls += 1
        return self._objects


def test_fallback_provider_uses_the_secondary_source() -> None:
    fallback_object = GaiaObject(source_id="gaia-fallback", ra_deg=10.7, dec_deg=41.27)
    provider = FallbackGaiaProvider(
        _FailingProvider("429"),
        _StaticProvider([fallback_object]),
    )

    objects = provider.search_cone(_CENTER, 120.0)

    assert objects == [fallback_object]


def test_fallback_provider_reports_both_failures() -> None:
    provider = FallbackGaiaProvider(
        _FailingProvider("429"),
        _FailingProvider("vizier down"),
    )

    with pytest.raises(GaiaQueryError, match="Gaia and VizieR failed"):
        provider.search_cone(_CENTER, 120.0)


def test_vizier_gaia_rows_are_normalized() -> None:
    table = Table(
        {
            "Source": [381267034301640832],
            "RA_ICRS": [10.70181959353],
            "DE_ICRS": [41.27078661875],
            "Gmag": [20.599688],
        }
    )

    objects = _vizier_gaia_objects(table)

    assert objects == [
        GaiaObject(
            source_id="381267034301640832",
            ra_deg=10.70181959353,
            dec_deg=41.27078661875,
            gmag=20.599688,
        )
    ]
