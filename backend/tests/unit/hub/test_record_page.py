from datetime import UTC, datetime
from uuid import uuid4

from astroimage.fits.schema import FitsRecordSummarySchema
from astroimage.hub.record_page import filter_summaries, page_summaries


def _summary(name: str, instrument: str | None, size: int) -> FitsRecordSummarySchema:
    return FitsRecordSummarySchema(
        record_id=uuid4(),
        slug=name,
        name=name,
        display_name=name,
        instrument=instrument,
        proposal_id="1",
        filters=None,
        observed_at=None,
        created_at=datetime(2026, 9, 1, tzinfo=UTC),
        size_bytes=size,
        data_uri=f"mast:{name}",
    )


def test_filter_matches_catalog_fields() -> None:
    records = [
        _summary("hst_a.fits", "WFC3", 10),
        _summary("hst_b.fits", "ACS", 20),
    ]
    records[0] = records[0].model_copy(
        update={
            "display_name": "Galaxia M31",
            "proposal_id": "12058",
            "data_uri": "mast:HST/product/hst_a.fits",
        }
    )
    assert [record.name for record in filter_summaries(records, "m31")] == ["hst_a.fits"]
    assert [record.name for record in filter_summaries(records, "wfc")] == ["hst_a.fits"]
    assert [record.name for record in filter_summaries(records, "12058")] == ["hst_a.fits"]
    assert [record.name for record in filter_summaries(records, "mast:hst_b")] == ["hst_b.fits"]


def test_page_puts_missing_instruments_last_and_slices() -> None:
    records = [
        _summary("b.fits", "WFC3", 20),
        _summary("a.fits", None, 5),
        _summary("c.fits", "ACS", 9),
    ]
    page = page_summaries(records, page=1, limit=2, sort="instrument", order="asc")
    assert [record.name for record in page.records] == ["c.fits", "b.fits"]
    assert page.has_more is True
    next_page = page_summaries(records, page=2, limit=2, sort="instrument", order="asc")
    assert [record.name for record in next_page.records] == ["a.fits"]
