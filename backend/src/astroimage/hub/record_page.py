from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from astroimage.fits.schema import FitsRecordSummarySchema
from astroimage.hub.schema import CandidateSortOrder, ListRecordsResponseSchema, RecordSortField
from astroimage.hub.sorting import sort_by_key

_RECORD_VALUE: dict[
    RecordSortField,
    Callable[[FitsRecordSummarySchema], str | int | datetime | None],
] = {
    "product_filename": lambda record: record.name,
    "instrument": lambda record: record.instrument,
    "proposal_id": lambda record: record.proposal_id,
    "filters": lambda record: record.filters,
    "size_bytes": lambda record: record.size_bytes,
    "observed_at": lambda record: record.observed_at,
    "display_name": lambda record: record.display_name,
    "created_at": lambda record: record.created_at,
}


def _sort_value(
    record: FitsRecordSummarySchema,
    sort: RecordSortField,
) -> str | int | datetime | None:
    return _RECORD_VALUE[sort](record)


def filter_summaries(
    records: list[FitsRecordSummarySchema],
    query: str,
) -> list[FitsRecordSummarySchema]:
    needle = query.casefold().strip()
    if needle == "":
        return records
    return [record for record in records if _matches_query(record, needle)]


def _matches_query(record: FitsRecordSummarySchema, needle: str) -> bool:
    values = (
        record.display_name,
        record.name,
        record.description or "",
        record.instrument or "",
        record.proposal_id or "",
        record.data_uri or "",
        *record.tags,
    )
    return any(needle in value.casefold() for value in values)


def page_summaries(
    records: list[FitsRecordSummarySchema],
    *,
    page: int,
    limit: int,
    sort: RecordSortField,
    order: CandidateSortOrder,
) -> ListRecordsResponseSchema:
    ordered = sort_by_key(records, key=lambda record: _sort_value(record, sort), order=order)
    start = (page - 1) * limit
    return ListRecordsResponseSchema(
        records=ordered[start : start + limit],
        page=page,
        limit=limit,
        has_more=len(ordered) > start + limit,
        sort=sort,
        order=order,
    )
