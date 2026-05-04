from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Voice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "voices"

    parent_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        index=True,
    )
    helper_profile_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("helper_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    provider: Mapped[str | None] = mapped_column(String(80))
    provider_voice_id: Mapped[str | None] = mapped_column(String(255))
    sample_url: Mapped[str | None] = mapped_column(Text)
    consent_record_url: Mapped[str | None] = mapped_column(Text)
    consent_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_recording_key: Mapped[str | None] = mapped_column(Text)
    sample_recording_key: Mapped[str | None] = mapped_column(Text)
    preview_audio_key: Mapped[str | None] = mapped_column(Text)
    approved_for_child_use: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")

    helper_profile: Mapped["HelperProfile"] = relationship(back_populates="voice")
    parent: Mapped["Parent | None"] = relationship()
