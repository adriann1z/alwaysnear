from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin


class HelperProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "helper_profiles"

    parent_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    child_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("children.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    parent: Mapped["Parent"] = relationship(back_populates="helper_profiles")
    child: Mapped["Child"] = relationship(back_populates="helper_profiles")
    avatar: Mapped["Avatar | None"] = relationship(
        back_populates="helper_profile",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    voice: Mapped["Voice | None"] = relationship(
        back_populates="helper_profile",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="helper_profile")
