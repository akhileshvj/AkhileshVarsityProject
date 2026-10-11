import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - only used before dependencies are installed
    Vector = None


class PersonaProfile(Base):
    __tablename__ = "persona_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    lifestyle_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    core_values: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    dealbreakers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    embedding = mapped_column(
        JSON if Vector is None else Vector(1536).with_variant(JSON, "sqlite"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="persona")
