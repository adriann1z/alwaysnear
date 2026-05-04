from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Child(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "children"

    parent_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(120))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    pronouns: Mapped[str | None] = mapped_column(String(80))
    comfort_notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    parent: Mapped["Parent"] = relationship(back_populates="children")
    helper_profiles: Mapped[list["HelperProfile"]] = relationship(
        back_populates="child",
        cascade="all, delete-orphan",
    )
    comfort_modes: Mapped[list["ComfortMode"]] = relationship(
        back_populates="child",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="child")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="child")
