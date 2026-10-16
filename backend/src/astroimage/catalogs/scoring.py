from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

# Scoring constants ported from the reference notebook
# `notebooks/busqueda-papers.ipynb` (TPI-Prueba). Keep them in parity: the
# ranking is dominated by identifier (50) and spatial (<=50) evidence, with the
# paper/DOI signals acting as tie-breakers.

IDENTIFIER_SCORE = 50.0
PAPER_SCORE = 25.0
DOI_SCORE = 15.0

MATCH_TYPE_OBJECT_IN_TABLE = "OBJECT_IN_TABLE"
MATCH_TYPE_CATALOGUE_ONLY = "CATALOGUE_ONLY"

_NON_IDENTIFIER = re.compile(r"[^0-9a-z]+")


def separation_score(separation_arcsec: float | None) -> float:
    if separation_arcsec is None:
        return 0.0
    if separation_arcsec < 0.1:
        return 50.0
    if separation_arcsec < 0.5:
        return 40.0
    if separation_arcsec < 1.0:
        return 30.0
    if separation_arcsec < 2.0:
        return 20.0
    if separation_arcsec < 5.0:
        return 10.0
    if separation_arcsec <= 10.0:
        return 5.0
    return 0.0


def identifier_score(matched: bool) -> float:
    return IDENTIFIER_SCORE if matched else 0.0


def paper_score(paper_bibcode: str | None) -> float:
    return PAPER_SCORE if paper_bibcode else 0.0


def doi_score(paper_doi: str | None) -> float:
    return DOI_SCORE if paper_doi else 0.0


def total_score(
    *,
    spatial: float,
    identifier: float,
    paper: float,
    doi: float,
) -> float:
    return spatial + identifier + paper + doi


def classify_match(has_object_in_table: bool, paper_bibcode: str | None) -> str:
    if has_object_in_table and paper_bibcode:
        return MATCH_TYPE_OBJECT_IN_TABLE
    return MATCH_TYPE_CATALOGUE_ONLY


def normalize_identifier(value: object) -> str:
    """Fold an identifier for tolerant cross-column matching.

    Gaia source ids, 2MASS designations and compact aliases normalise to the
    same alphanumeric token regardless of separators or case.
    """
    return _NON_IDENTIFIER.sub("", str(value).lower())


def find_identifiers_in_row(
    values: Iterable[tuple[str, str]],
    known_identifiers: Iterable[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Scan a row's columns for any of the known identifiers.

    Returns the matched identifiers (original spelling) and the columns where
    they were found, both de-duplicated and order-preserving.
    """
    normalized_known: Mapping[str, str] = {
        normalize_identifier(identifier): identifier for identifier in known_identifiers
    }
    matched: list[str] = []
    columns: list[str] = []
    for column, text in values:
        for original_id in _identifiers_in_text(text, normalized_known):
            if original_id not in matched:
                matched.append(original_id)
            if column not in columns:
                columns.append(column)
    return tuple(matched), tuple(columns)


def _identifiers_in_text(text: str, normalized_known: Mapping[str, str]) -> list[str]:
    normalized_value = normalize_identifier(text)
    if not normalized_value:
        return []
    return [
        original_id
        for normalized_id, original_id in normalized_known.items()
        if normalized_id and normalized_id in normalized_value
    ]
