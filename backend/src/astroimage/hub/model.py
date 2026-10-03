from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, Float, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from astroimage.shared.database import Base


class TransferStatus(StrEnum):
    QUEUED = "queued"
    TRANSFERRING = "transferring"
    ANNOTATING = "annotating"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


ACTIVE_TRANSFER_STATUSES = (
    TransferStatus.QUEUED,
    TransferStatus.TRANSFERRING,
    TransferStatus.ANNOTATING,
    TransferStatus.STORING,
)

RESUMABLE_TRANSFER_STATUSES = (
    TransferStatus.INTERRUPTED,
    TransferStatus.FAILED,
    TransferStatus.CANCELLED,
)


class ImageTransfer(Base):
    __tablename__ = "image_transfers"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="mast")
    destination: Mapped[str] = mapped_column(String(32), nullable=False, default="astroimage")
    target_name: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    data_uri: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    product_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    observation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    proposal_id: Mapped[str] = mapped_column(String(128), nullable=False)
    instrument: Mapped[str | None] = mapped_column(String(128), nullable=True)
    filters: Mapped[str | None] = mapped_column(String(256), nullable=True)
    observed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ra_deg: Mapped[float] = mapped_column(Float, nullable=False)
    dec_deg: Mapped[float] = mapped_column(Float, nullable=False)
    bytes_transferred: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    etag: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(128), nullable=True)
    speed_bytes_per_second: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    record_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    slug: Mapped[str | None] = mapped_column(String(512), nullable=True)
    samples: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
