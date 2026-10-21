from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from astroimage.catalogs.model import (
    CatalogEvaluation,
    CatalogMetadata,
    CatalogRow,
    CatalogTable,
)
from astroimage.catalogs.readme import (
    ReadmeData,
    ads_url,
    clean_bibcode,
    clean_doi,
    determine_catalogue_bibcode,
    determine_paper_bibcode,
    determine_paper_doi,
    doi_url,
)
from astroimage.catalogs.scoring import (
    classify_match,
    doi_score,
    find_identifiers_in_row,
    identifier_score,
    paper_score,
    separation_score,
    total_score,
)


@dataclass(frozen=True)
class _ObjectRow:
    row: CatalogRow
    identifiers: tuple[str, ...]
    columns: tuple[str, ...]
    spatial_match: bool
    identifier_match: bool


@dataclass(frozen=True)
class _BestMatch:
    separation_arcsec: float | None
    object_identifier: str | None
    identifier_columns: str | None
    spatial_match: bool
    identifier_match: bool


def select_object_rows(
    table: CatalogTable,
    known_identifiers: list[str],
    search_radius_arcsec: float,
) -> list[_ObjectRow]:
    rows: list[_ObjectRow] = []
    for row in table.rows:
        identifiers, columns = find_identifiers_in_row(row.values, known_identifiers)
        spatial_match = (
            row.separation_arcsec is not None and row.separation_arcsec <= search_radius_arcsec
        )
        identifier_match = len(identifiers) > 0
        if spatial_match or identifier_match:
            rows.append(
                _ObjectRow(
                    row=row,
                    identifiers=identifiers,
                    columns=columns,
                    spatial_match=spatial_match,
                    identifier_match=identifier_match,
                )
            )
    return rows


def best_object_row(object_rows: list[_ObjectRow]) -> _ObjectRow | None:
    if not object_rows:
        return None
    return min(
        object_rows,
        key=lambda entry: (
            0 if entry.identifier_match else 1,
            entry.row.separation_arcsec if entry.row.separation_arcsec is not None else np.inf,
        ),
    )


def _best_match(best: _ObjectRow | None) -> _BestMatch:
    if best is None:
        return _BestMatch(None, None, None, False, False)
    return _BestMatch(
        separation_arcsec=best.row.separation_arcsec,
        object_identifier="; ".join(best.identifiers) if best.identifiers else None,
        identifier_columns="; ".join(best.columns) if best.columns else None,
        spatial_match=bool(best.spatial_match),
        identifier_match=bool(best.identifier_match),
    )


def score_catalogue(
    catalogue_id: str,
    metadata: CatalogMetadata,
    readme: ReadmeData | None,
    best: _ObjectRow | None,
) -> CatalogEvaluation:
    readme_data = readme or ReadmeData()
    catalogue_bibcode = determine_catalogue_bibcode(metadata.origin_article, readme_data)
    paper_bibcode = determine_paper_bibcode(metadata.origin_article, readme_data)
    paper_doi = determine_paper_doi(paper_bibcode, readme_data, metadata.doi)
    catalogue_doi = clean_doi(metadata.doi)
    match = _best_match(best)
    spatial = separation_score(match.separation_arcsec)
    identifier = identifier_score(match.identifier_match)
    paper = paper_score(paper_bibcode)
    doi = doi_score(paper_doi)
    description = readme_data.description or readme_data.abstract
    return CatalogEvaluation(
        catalogue_id=catalogue_id,
        metadata=metadata,
        match_type=classify_match(match.identifier_match, paper_bibcode or None),
        catalogue_description=description or None,
        catalogue_keywords=readme_data.keywords or None,
        separation_arcsec=match.separation_arcsec,
        object_found_in_table=match.identifier_match,
        object_identifier=match.object_identifier,
        identifier_columns=match.identifier_columns,
        spatial_match=match.spatial_match,
        identifier_match=match.identifier_match,
        spatial_score=spatial,
        identifier_score=identifier,
        paper_score=paper,
        doi_score=doi,
        total_score=total_score(spatial=spatial, identifier=identifier, paper=paper, doi=doi),
        catalogue_bibcode=clean_bibcode(catalogue_bibcode) or None,
        catalogue_doi=catalogue_doi or None,
        catalogue_doi_url=doi_url(catalogue_doi),
        paper_bibcode=clean_bibcode(paper_bibcode) or None,
        paper_doi=paper_doi or None,
        paper_doi_url=doi_url(paper_doi),
        paper_ads_url=ads_url(paper_bibcode),
        vizier_url=metadata.webpage,
        readme_url=readme_data.url,
        readme_bibcodes=readme_data.bibcodes,
        readme_dois=readme_data.dois,
    )


def rank_evaluations(
    pairs: list[tuple[CatalogEvaluation, CatalogTable]],
) -> list[CatalogEvaluation]:
    ordered = sorted(
        pairs,
        key=lambda pair: (
            -pair[0].total_score,
            not pair[0].object_found_in_table,
            not pair[0].identifier_match,
            pair[0].separation_arcsec if pair[0].separation_arcsec is not None else np.inf,
        ),
    )
    return [evaluation for evaluation, _ in ordered]
