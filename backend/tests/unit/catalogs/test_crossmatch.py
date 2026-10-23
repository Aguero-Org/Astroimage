from __future__ import annotations

import pytest

from astroimage.catalogs.crossmatch import crossmatch_catalog
from astroimage.catalogs.model import CatalogRow, DetectionCoordinate

ARCSEC_IN_DEGREES = 1.0 / 3600.0


def _row(
    index: int,
    ra: float,
    dec: float,
    *,
    values: tuple[tuple[str, str], ...] | None = None,
) -> CatalogRow:
    if values is None:
        values = (
            ("Name", f"TARGET-{index}"),
            ("_2MASS", f"2MASS J{index:07d}"),
        )
    return CatalogRow(
        index=index,
        ra_deg=ra,
        dec_deg=dec,
        separation_arcsec=0.0,
        values=values,
    )


def test_crossmatch_matches_closest_detection_within_radius() -> None:
    rows = (
        _row(0, 10.0, 20.0),
        _row(1, 10.5, 20.0),
    )
    detections = [
        DetectionCoordinate(source_id=7, object_type="point", ra_deg=10.0005, dec_deg=20.0),
    ]
    result = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=5.0)

    assert result.catalogue_id == "I/350"
    assert result.match_radius_arcsec == 5.0
    assert result.detection_count == 1
    assert result.matched_count == 1
    first = result.matches[0]
    assert first.catalogue_row_index == 0
    assert first.ra_deg == pytest.approx(10.0)
    assert first.dec_deg == pytest.approx(20.0)
    assert first.object_identifier == "TARGET-0"
    assert first.matched is True
    assert first.detection_source_id == 7
    assert first.object_type == "point"
    assert first.separation_arcsec is not None
    assert first.separation_arcsec < 5.0
    assert first.probability == pytest.approx((1.0 - first.separation_arcsec / 5.0) ** 2.0)
    second = result.matches[1]
    assert second.matched is False
    assert second.probability == 0.0
    assert second.detection_source_id is None
    assert second.object_type is None


def test_crossmatch_without_usable_rows_returns_empty() -> None:
    detections = [
        DetectionCoordinate(source_id=1, object_type="point", ra_deg=10.0, dec_deg=20.0),
    ]
    result = crossmatch_catalog(
        "I/350",
        (CatalogRow(index=0),),
        detections,
        match_radius_arcsec=2.5,
    )

    assert result.catalogue_id == "I/350"
    assert result.match_radius_arcsec == 2.5
    assert result.matches == ()
    assert result.detection_count == 1
    assert result.matched_count == 0


def test_crossmatch_without_detections_returns_empty() -> None:
    result = crossmatch_catalog(
        "I/350",
        (_row(0, 10.0, 20.0),),
        [],
        match_radius_arcsec=2.5,
    )

    assert result.catalogue_id == "I/350"
    assert result.match_radius_arcsec == 2.5
    assert result.matches == ()
    assert result.detection_count == 0
    assert result.matched_count == 0


def test_crossmatch_rejects_partially_missing_coordinates() -> None:
    rows = (
        CatalogRow(index=0, ra_deg=10.0),
        CatalogRow(index=1, dec_deg=20.0),
    )
    detections = [
        DetectionCoordinate(source_id=1, object_type="point", ra_deg=10.0, dec_deg=20.0),
    ]
    result = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=5.0)

    assert result.matches == ()
    assert result.matched_count == 0


def test_crossmatch_skips_invalid_rows_before_later_matches() -> None:
    rows = (
        CatalogRow(index=0),
        _row(1, 10.0, 20.0),
    )
    detections = [
        DetectionCoordinate(source_id=1, object_type="point", ra_deg=10.0, dec_deg=20.0),
    ]
    result = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=5.0)

    assert [match.catalogue_row_index for match in result.matches] == [1]
    assert result.matched_count == 1


def test_crossmatch_counts_every_matched_row() -> None:
    rows = (
        _row(0, 10.0, 20.0),
        _row(1, 10.5, 20.0),
    )
    detections = [
        DetectionCoordinate(source_id=7, object_type="point", ra_deg=10.0, dec_deg=20.0),
        DetectionCoordinate(source_id=8, object_type="point", ra_deg=10.5, dec_deg=20.0),
    ]
    result = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=1.0)

    assert result.matched_count == 2
    assert [match.detection_source_id for match in result.matches] == [7, 8]


def test_crossmatch_includes_separation_equal_to_radius() -> None:
    rows = (_row(0, 0.0, 0.0),)
    detections = [
        DetectionCoordinate(source_id=1, object_type="point", ra_deg=0.001, dec_deg=0.0),
    ]
    initial = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=10.0)
    separation = initial.matches[0].separation_arcsec
    assert separation is not None

    result = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=separation)

    assert result.matches[0].matched is True
    assert result.matches[0].probability == 0.0


def test_crossmatch_clamps_zero_radius_to_positive_value() -> None:
    rows = (_row(0, 0.0, 0.0),)
    detections = [
        DetectionCoordinate(
            source_id=1,
            object_type="point",
            ra_deg=0.5 * ARCSEC_IN_DEGREES,
            dec_deg=0.0,
        ),
    ]
    result = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=0.0)

    assert result.matches[0].matched is False
    assert result.matches[0].probability == 0.0
    assert result.matches[0].detection_source_id is None


def test_crossmatch_clamps_zero_probability_power_to_positive_value() -> None:
    rows = (_row(0, 0.0, 0.0),)
    detections = [
        DetectionCoordinate(source_id=1, object_type="point", ra_deg=0.001, dec_deg=0.0),
    ]
    result = crossmatch_catalog(
        "I/350",
        rows,
        detections,
        match_radius_arcsec=10.0,
        probability_power=0.0,
    )
    separation = result.matches[0].separation_arcsec
    assert separation is not None

    expected = (1.0 - separation / 10.0) ** 0.1
    assert result.matches[0].probability == pytest.approx(expected)


def test_crossmatch_uses_first_visible_text_identifier() -> None:
    rows = (
        CatalogRow(
            index=0,
            ra_deg=0.0,
            dec_deg=0.0,
            values=(
                ("_2MASS", "2MASS J00000001"),
                ("Name", "TARGET"),
                ("Numeric", "12345"),
                ("Alias", "OTHER"),
            ),
        ),
    )
    detections = [
        DetectionCoordinate(source_id=1, object_type="point", ra_deg=0.0, dec_deg=0.0),
    ]
    result = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=1.0)

    assert result.matches[0].object_identifier == "TARGET"


def test_crossmatch_without_visible_text_identifier_returns_none() -> None:
    rows = (
        CatalogRow(
            index=0,
            ra_deg=0.0,
            dec_deg=0.0,
            values=(
                ("_2MASS", "2MASS J00000001"),
                ("Numeric", "12345"),
            ),
        ),
    )
    detections = [
        DetectionCoordinate(source_id=1, object_type="point", ra_deg=0.0, dec_deg=0.0),
    ]
    result = crossmatch_catalog("I/350", rows, detections, match_radius_arcsec=1.0)

    assert result.matches[0].object_identifier is None
