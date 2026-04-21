"""
app/models/personalization.py
─────────────────────────────
ORM model for the ``personalizations`` table (FR18–FR21).

Stores the personal touches a user adds to a basket:
* Custom gift message (≤ 250 characters).
* Ribbon color from a predefined palette.
* Uploaded gift-tag image URL (stored in Supabase Storage).
* Requested delivery date.
"""

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

    # ── Parent basket ────────────────────────────────────────────────
    basket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("baskets.id", ondelete="CASCADE"),
        nullable=False, unique=True,
        doc="One personalization per basket.",
    )

    # ── Gift message (FR18) ──────────────────────────────────────────
    gift_message: Mapped[str] = mapped_column(
        String(250), nullable=True, default="",
        doc="Custom note included with the gift (max 250 chars).",
    )

    # ── Ribbon color (FR19) ──────────────────────────────────────────
    ribbon_color: Mapped[str] = mapped_column(
        String(30), nullable=True, default="",
        doc="Chosen ribbon color (e.g. 'red', 'gold', 'pink').",
    )

    # ── Gift-tag image (FR20) ────────────────────────────────────────
    gift_tag_image_url: Mapped[str] = mapped_column(
        String(500), nullable=True, default="",
        doc="Public URL of the uploaded gift-tag image.",
    )

    # ── Delivery date (FR21) ─────────────────────────────────────────
    requested_delivery_date: Mapped[date] = mapped_column(
        Date, nullable=True,
        doc="Preferred delivery date selected via calendar picker.",
    )

    # ── Timestamps ───────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────
    basket = relationship("Basket", back_populates="personalization")

    def __repr__(self) -> str:
        return f"<Personalization basket_id={self.basket_id!r}>"
