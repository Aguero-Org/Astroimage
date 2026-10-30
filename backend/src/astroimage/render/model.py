from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from astroimage.shared.database import Base


class ImagePreview(Base):
    __tablename__ = "image_previews"
    __table_args__ = (
        UniqueConstraint(
            "record_id",
            "preset_id",
            "edge_px",
            name="uq_image_previews_record_preset_edge",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    record_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("fits_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    preset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    edge_px: Mapped[int] = mapped_column(Integer, nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
