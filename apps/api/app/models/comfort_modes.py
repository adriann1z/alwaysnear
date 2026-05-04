from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ComfortMode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "comfort_modes"

    child_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("children.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    routine_prompt: Mapped[str | None] = mapped_column(Text)
    safety_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    parent_approval_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    child: Mapped["Child"] = relationship(back_populates="comfort_modes")

    @property
    def mode_name(self) -> str:
        return self.name

    @property
    def script(self) -> str | None:
        return self.routine_prompt

    @property
    def active(self) -> bool:
        return self.is_active
