from __future__ import annotations

import pytest

from astroimage.catalogs.scoring import (
    classify_match,
    doi_score,
    find_identifiers_in_row,
    identifier_score,
    normalize_identifier,
    paper_score,
    separation_score,
    total_score,
)


@pytest.mark.parametrize(
    ("separation", "expected"),
    [
        (None, 0.0),
        (0.05, 50.0),
        (0.4, 40.0),
        (0.9, 30.0),
        (1.5, 20.0),
        (4.9, 10.0),
        (10.0, 5.0),
        (10.1, 0.0),
    ],
)
def test_separation_score_matches_reference_buckets(
    separation: float | None,
    expected: float,
) -> None:
    assert separation_score(separation) == expected


def test_identifier_paper_and_doi_scores_only_trigger_on_evidence() -> None:
    assert identifier_score(True) == 50.0
    assert identifier_score(False) == 0.0
    assert paper_score("2016A&A...595A...1G") == 25.0
    assert paper_score("") == 0.0
    assert doi_score("10.1051/0004-6361/201629272") == 15.0
    assert doi_score("") == 0.0


def test_total_score_adds_the_signals() -> None:
    assert total_score(spatial=40.0, identifier=50.0, paper=25.0, doi=15.0) == 130.0


def test_classify_match_requires_object_and_paper() -> None:
    assert classify_match(True, "2016A&A...595A...1G") == "OBJECT_IN_TABLE"
    assert classify_match(True, None) == "CATALOGUE_ONLY"
    assert classify_match(False, "2016A&A...595A...1G") == "CATALOGUE_ONLY"


def test_normalize_identifier_folds_separators_and_case() -> None:
    assert normalize_identifier("2MASS J05342669+2200301") == "2massj053426692200301"
    assert normalize_identifier("05342669+2200301") in normalize_identifier(
        "2MASS J05342669+2200301"
    )


def test_find_identifiers_in_row_reports_identifiers_and_columns() -> None:
    values = (
        ("_2MASS", "2MASS J05342669+2200301"),
        ("Source", "3403818138212571264"),
        ("Name", "Unrelated"),
    )
    identifiers, columns = find_identifiers_in_row(
        values,
        ["3403818138212571264", "2MASS J05342669+2200301"],
    )
    assert identifiers == ("2MASS J05342669+2200301", "3403818138212571264")
    assert columns == ("_2MASS", "Source")


def test_find_identifiers_in_row_returns_empty_without_matches() -> None:
    identifiers, columns = find_identifiers_in_row(
        (("_2MASS", "2MASS J00000000+0000000"),),
        ["3403818138212571264"],
    )
    assert identifiers == ()
    assert columns == ()
