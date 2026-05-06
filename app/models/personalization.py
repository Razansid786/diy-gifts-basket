
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import String, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Personalization(Base):
    __tablename__ = "personalizations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    basket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("baskets.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )

    gift_message: Mapped[str] = mapped_column(String(250), nullable=True, default="")
    ribbon_color: Mapped[str] = mapped_column(String(30), nullable=True, default="")
    gift_tag_image_url: Mapped[str] = mapped_column(String(500), nullable=True, default="")

    requested_delivery_date: Mapped[date] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    basket = relationship("Basket", back_populates="personalization")

    def __repr__(self) -> str:
        return f"<Personalization basket_id={self.basket_id!r}>"
