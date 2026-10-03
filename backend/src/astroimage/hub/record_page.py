from __future__ import annotations

from datetime import datetime

from astroimage.fits.schema import FitsRecordSummarySchema
from astroimage.hub.schema import CandidateSortOrder, ListRecordsResponseSchema, RecordSortField
from astroimage.hub.sorting import sort_by_key


def _sort_value(
    record: FitsRecordSummarySchema,
    sort: RecordSortField,
) -> str | int | datetime | None:
    if sort == "product_filename":
        return record.name
    if sort == "instrument":
        return record.instrument
    if sort == "proposal_id":
        return record.proposal_id
    if sort == "filters":
        return record.filters
    if sort == "size_bytes":
        return record.size_bytes
    if sort == "observed_at":
        return record.observed_at
    if sort == "display_name":
        return record.display_name
    return record.created_at


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
        record.instrument or "",
        record.proposal_id,
        record.data_uri,
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
