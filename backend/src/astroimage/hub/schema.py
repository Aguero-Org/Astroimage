from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from astroimage.fits.schema import FitsRecordSummarySchema


class FetchImageResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID


class ListRecordsResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[FitsRecordSummarySchema]
