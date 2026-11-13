from __future__ import annotations

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from astroimage.simbad import provider as provider_module
from astroimage.simbad.provider import (
    AstroquerySimbadProvider,
    SimbadQueryError,
    _object_type_clause,
    aliases_from_table,
    objects_from_table,
    references_from_table,
)


def _region_table() -> Table:
    return Table(
        {
            "main_id": ["M   1"],
            "ra": [83.6324],
            "dec": [22.0174],
            "otype": ["SNR"],
            "otype_txt": ["SuperNova Remnant"],
            "sp_type": [None],
            "plx_value": [np.nan],
            "plx_err": [None],
            "galdim_majaxis": [7.0],
            "galdim_minaxis": [5.0],
            "galdim_angle": [None],
            "rvz_radvel": [None],
            "rvz_redshift": [None],
            "rvz_type": [None],
            "nbref": [6602],
            "separation_deg": [0.001],
        }
    )


def test_objects_from_table_normalizes_rows() -> None:
    objects = objects_from_table(_region_table())

    assert len(objects) == 1
    obj = objects[0]
    assert obj.main_id == "M   1"
    assert obj.ra_deg == pytest.approx(83.6324)
    assert obj.dec_deg == pytest.approx(22.0174)
    assert obj.separation_arcsec == pytest.approx(3.6)
    assert obj.spectral_type is None
    assert obj.parallax_mas is None
    assert obj.major_axis_arcmin == 7.0
    assert obj.reference_count == 6602


def test_objects_from_table_skips_rows_without_position() -> None:
    table = _region_table()
    table["dec"] = [None]

    assert objects_from_table(table) == []


def test_aliases_and_references_from_tables() -> None:
    alias_table = Table(
        {
            "main_id": ["M   1", "M   1"],
            "id": ["M 1", "Gaia DR3 123456"],
        }
    )
    reference_table = Table(
        {
            "main_id": ["M   1"],
            "bibcode": ["2024A&A...2B"],
            "year": [2024],
            "title": [None],
            "doi": ["10.1000/example"],
            "journal": ["A&A"],
            "nbobject": [12],
        }
    )

    aliases = aliases_from_table(alias_table)
    references = references_from_table(reference_table)

    assert [alias.name for alias in aliases] == ["M 1", "Gaia DR3 123456"]
    assert references[0].object_id == "M   1"
    assert references[0].year == 2024
    assert references[0].title is None
    assert references[0].doi == "10.1000/example"
    assert references[0].object_count == 12


def test_object_type_clause_only_accepts_codes() -> None:
    assert _object_type_clause("snr") == "AND basic.otype = 'SNR'"
    assert _object_type_clause(None) == ""
    with pytest.raises(ValueError):
        _object_type_clause("SNR' OR 1=1")


def _fake_simbad_class(calls: list[tuple[str, str, int]]) -> type:
    class FakeSimbad:
        def __init__(self) -> None:
            self.server = ""
            self.TIMEOUT = 0

        def query_tap(self, query: str, *, maxrec: int) -> Table:
            calls.append((self.server, query, maxrec))
            if self.server == "simbad.cds.unistra.fr":
                raise RuntimeError("primary unavailable")
            return _region_table()

    return FakeSimbad


def test_query_region_falls_back_to_the_next_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, int]] = []
    monkeypatch.setattr(
        provider_module,
        "SimbadClass",
        _fake_simbad_class(calls),
    )
    provider = AstroquerySimbadProvider(servers=["simbad.cds.unistra.fr", "simbad.harvard.edu"])

    objects = provider.query_region(
        SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg, frame="icrs"),
        60.0,
        row_limit=5,
    )

    assert [call[0] for call in calls] == [
        "simbad.cds.unistra.fr",
        "simbad.harvard.edu",
    ]
    assert calls[1][2] == 5
    assert objects[0].main_id == "M   1"


def test_query_region_raises_when_every_server_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, int]] = []

    class FailingSimbad:
        def __init__(self) -> None:
            self.server = ""
            self.TIMEOUT = 0

        def query_tap(self, query: str, *, maxrec: int) -> Table:
            calls.append((self.server, query, maxrec))
            raise RuntimeError(f"{self.server} unavailable")

    monkeypatch.setattr(provider_module, "SimbadClass", FailingSimbad)
    provider = AstroquerySimbadProvider(servers=["one.example.org", "two.example.org"])

    with pytest.raises(SimbadQueryError, match="two.example.org unavailable"):
        provider.query_region(
            SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg, frame="icrs"),
            60.0,
            row_limit=5,
        )

    assert len(calls) == 2
