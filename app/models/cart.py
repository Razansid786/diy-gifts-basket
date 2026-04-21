"""
app/models/cart.py
──────────────────
ORM models for the shopping cart (FR22).

``Cart``
    One cart per user (or per guest session).

``CartItem``
    Each item in the cart references a completed ``Basket``.
    The user can adjust the quantity of each basket before checkout.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Owner ────────────────────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True, unique=True,
        doc="FK to users; NULL for guests.",
    )
    session_id: Mapped[str] = mapped_column(
        String(100), nullable=True,
        doc="Browser session ID for guest carts.",
    )

    # ── Timestamps ───────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────
    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Cart id={self.id!r} user_id={self.user_id!r}>"


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    cart_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False,
    )
    basket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("baskets.id", ondelete="CASCADE"), nullable=False,
        doc="Each cart item is a completed gift basket.",
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
    )

    # ── Relationships ────────────────────────────────────────────────
    cart = relationship("Cart", back_populates="items")
    basket = relationship("Basket")

    def __repr__(self) -> str:
        return f"<CartItem cart={self.cart_id!r} basket={self.basket_id!r} qty={self.quantity}>"
