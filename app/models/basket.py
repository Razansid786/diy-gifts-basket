
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class GiftBase(Base):

    __tablename__ = "bases"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        doc="e.g. 'Wicker Basket', 'Gift Box', 'Decorative Tin'.",
    )
    size: Mapped[str] = mapped_column(
        String(10), nullable=False,
        doc="S, M, or L — determines max_items.",
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Price of the container itself.",
    )
    image_url: Mapped[str] = mapped_column(
        String(500), nullable=True, default="",
    )
    max_items: Mapped[int] = mapped_column(
        Integer, nullable=False,
        doc="Maximum number of gift items this container can hold (FR14).",
    )

    baskets = relationship("Basket", back_populates="base")

    def __repr__(self) -> str:
        return f"<GiftBase id={self.id!r} name={self.name!r} size={self.size!r}>"

class Basket(Base):

    __tablename__ = "baskets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="FK to users; NULL for guest builders.",
    )
    session_id: Mapped[str] = mapped_column(
        String(100), nullable=True,
        doc="Browser session ID for guest builders.",
    )

    base_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bases.id", ondelete="SET NULL"),
        nullable=True,
        doc="FK to the selected gift base (FR12).",
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft",
        doc="'draft' while building, 'complete' when ready for cart.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="baskets")
    base = relationship("GiftBase", back_populates="baskets")
    items = relationship("BasketItem", back_populates="basket", cascade="all, delete-orphan")
    personalization = relationship(
        "Personalization", back_populates="basket",
        uselist=False, cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Basket id={self.id!r} status={self.status!r}>"

class BasketItem(Base):

    __tablename__ = "basket_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    basket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("baskets.id", ondelete="CASCADE"), nullable=False,
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
    )

    basket = relationship("Basket", back_populates="items")
    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<BasketItem basket={self.basket_id!r} product={self.product_id!r} qty={self.quantity}>"