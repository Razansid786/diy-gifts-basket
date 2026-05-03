
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        doc="FK to the owning user.",
    )

    label: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Home",
        doc="Friendly label (e.g. 'Home', 'Office').",
    )
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="US")

    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="If True, this address is pre-selected at checkout.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address id={self.id!r} label={self.label!r} city={self.city!r}>"