from __future__ import annotations

import pytest
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
