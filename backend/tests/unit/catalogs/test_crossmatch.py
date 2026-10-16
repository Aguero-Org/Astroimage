from __future__ import annotations

from astroimage.catalogs.crossmatch import crossmatch_catalog
from astroimage.catalogs.model import CatalogRow, DetectionCoordinate


def _row(index: int, ra: float, dec: float) -> CatalogRow:
    return CatalogRow(
        index=index,
        ra_deg=ra,
        dec_deg=dec,
        separation_arcsec=0.0,
        values=(("_2MASS", f"2MASS J{index:07d}"),),
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
    assert result.detection_count == 1
    assert result.matched_count == 1
    first = result.matches[0]
    assert first.matched is True
    assert first.detection_source_id == 7
    assert first.object_type == "point"
    assert first.separation_arcsec is not None
    assert first.separation_arcsec < 5.0
    assert 0.0 < first.probability <= 1.0
    assert result.matches[1].matched is False


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
    assert result.matches == ()
    assert result.detection_count == 1
    assert result.matched_count == 0
