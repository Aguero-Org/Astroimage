from __future__ import annotations

from astroimage.catalogs.evaluation import score_catalogue
from astroimage.catalogs.model import CatalogMetadata
from astroimage.catalogs.readme import ReadmeData


def test_score_catalogue_uses_the_readme_title_when_metadata_has_none() -> None:
    evaluation = score_catalogue(
        "I/61B/agk3",
        CatalogMetadata(catalogue_id="I/61B/agk3"),
        ReadmeData(title=" AGK3 Catalogue "),
        None,
    )

    assert evaluation.metadata.title == "AGK3 Catalogue"


def test_score_catalogue_keeps_a_metadata_title() -> None:
    evaluation = score_catalogue(
        "I/350",
        CatalogMetadata(catalogue_id="I/350", title="Gaia EDR3"),
        ReadmeData(title="Other"),
        None,
    )

    assert evaluation.metadata.title == "Gaia EDR3"
