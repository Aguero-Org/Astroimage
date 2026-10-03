from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from astroimage.fits.schema import FitsRecordSummarySchema

CandidateSortField = Literal[
    "product_filename",
    "instrument",
    "proposal_id",
    "filters",
    "size_bytes",
    "observed_at",
]
CandidateSortOrder = Literal["asc", "desc"]


def _stripped(value: str) -> str:
    return value.strip()


RecordSortField = Literal[
    "product_filename",
    "instrument",
    "proposal_id",
    "filters",
    "size_bytes",
    "observed_at",
    "display_name",
    "created_at",
]


class FetchImageResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID
    slug: str


class ListRecordsResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[FitsRecordSummarySchema]
    page: int = 1
    limit: int = 100
    has_more: bool = False
    sort: RecordSortField = "created_at"
    order: CandidateSortOrder = "desc"


class CandidateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    product_filename: str
    instrument: str | None
    proposal_id: str
    observation_id: str
    filters: str | None
    observed_at: str | None
    size_bytes: int | None
    ra_deg: float
    dec_deg: float
    data_uri: str


class CandidatePageSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CandidateSchema]
    page: int
    limit: int
    has_more: bool
    sort: CandidateSortField
    order: CandidateSortOrder


class SelectCandidateRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_token: str
    display_name: Annotated[
        str,
        BeforeValidator(_stripped),
        Field(min_length=1, max_length=256),
    ]


class TransferStatusSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transfer_id: UUID
    status: str
    display_name: str
    product_filename: str
    bytes_transferred: int
    total_bytes: int | None
    speed_bytes_per_second: float | None
    progress: float | None
    error: str | None
    record_id: UUID | None
    slug: str | None
    resumable: bool
