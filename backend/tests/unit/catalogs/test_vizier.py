from __future__ import annotations

import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table

from astroimage.catalogs.vizier import (
    AstroqueryVizierProvider,
    metadata_catalog_candidates,
)


def test_metadata_catalog_candidates_adds_the_parent_of_a_table_id() -> None:
    assert metadata_catalog_candidates("I/61B/agk3") == ("I/61B/agk3", "I/61B")
    assert metadata_catalog_candidates("I/350") == ("I/350",)
    assert metadata_catalog_candidates("  /  ") == ()


def test_catalog_metadata_uses_the_parent_title(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_metadata(*, catalog: str) -> Table:
        if catalog.count("/") >= 2:
            raise LookupError(catalog)
        return Table({"title": ["AGK3 Catalogue"]})

    monkeypatch.setattr(
        "astroimage.catalogs.vizier.Vizier.get_catalog_metadata",
        fake_metadata,
    )

    metadata = AstroqueryVizierProvider().catalog_metadata("I/61B/agk3")

    assert metadata.catalogue_id == "I/61B/agk3"
    assert metadata.title == "AGK3 Catalogue"


def test_query_region_uses_the_next_mirror_when_the_first_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeVizier:
        def __init__(self, *, columns: list[str], row_limit: int, vizier_server: str) -> None:
            self.columns = columns
            self.row_limit = row_limit
            self.server = vizier_server
            self.TIMEOUT = 0

        def query_region(self, center: SkyCoord, radius: object, *, cache: bool) -> list[Table]:
            calls.append(self.server)
            assert "*" not in self.columns
            assert cache is False
            if self.server == "vizier.cds.unistra.fr":
                raise TimeoutError(self.server)
            table = Table({"_r": [0.2]})
            table.meta["name"] = "I/350/gaia"
            return [table]

    monkeypatch.setattr("astroimage.catalogs.vizier.Vizier", FakeVizier)
    catalogs = AstroqueryVizierProvider().query_region(
        SkyCoord(ra=10.0, dec=41.0, unit="deg"),
        10.0,
        row_limit=50,
    )

    assert calls == ["vizier.cds.unistra.fr", "vizier.cfa.harvard.edu"]
    assert [catalog.catalogue_id for catalog in catalogs] == ["I/350/gaia"]
