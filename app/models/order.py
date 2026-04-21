"""
app/models/order.py
───────────────────
ORM models for orders (FR23–FR30).

``Order``
    Created during checkout.  Stores the shipping address as a JSON
    snapshot (so the original data is preserved even if the user later
    modifies their saved addresses).

``OrderItem``
    Links an order to the specific baskets that were purchased.
    The admin uses this for the "Packing List" view (FR29).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Numeric, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Owner ────────────────────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="NULL for guest checkout (FR5).",
    )
    guest_email: Mapped[str] = mapped_column(
        String(255), nullable=True,
        doc="Email provided during guest checkout.",
    )

    # ── Shipping ─────────────────────────────────────────────────────
    shipping_address_json: Mapped[str] = mapped_column(
        Text, nullable=False,
        doc="JSON snapshot of the shipping address at time of order.",
    )
    shipping_fee: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0,
        doc="Calculated shipping cost (FR23).",
    )

    # ── Totals ───────────────────────────────────────────────────────
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Sum of item prices before shipping.",
    )
    total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Final amount = subtotal + shipping_fee.",
    )

    # ── Status ───────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending",
        doc="Order lifecycle: pending → processing → shipped → delivered.",
    )

    # ── Payment ──────────────────────────────────────────────────────
    payment_ref: Mapped[str] = mapped_column(
        String(100), nullable=True,
        doc="Simulated payment reference / transaction ID (FR25).",
    )

    # ── Timestamps ───────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Also serves as the order date for sorting (FR28).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order id={self.id!r} status={self.status!r} total={self.total}>"


class OrderItem(Base):
    """
    Line item linking an order to a purchased basket.

    ``unit_price`` is captured at order time so historical records
    remain accurate even if product prices change later.
    """
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False,
    )
    basket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("baskets.id", ondelete="SET NULL"), nullable=True,
        doc="The gift basket that was ordered (admin packing list — FR29).",
    )
    unit_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Total price of this basket at time of purchase.",
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
    )

    # ── Relationships ────────────────────────────────────────────────
    order = relationship("Order", back_populates="items")
    basket = relationship("Basket")

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id!r} basket={self.basket_id!r}>"
