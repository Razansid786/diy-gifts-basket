
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

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    guest_email: Mapped[str] = mapped_column(String(255), nullable=True)

    shipping_address_json: Mapped[str] = mapped_column(Text, nullable=False)
    shipping_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")

    payment_ref: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order id={self.id!r} status={self.status!r} total={self.total}>"

class OrderItem(Base):

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
    )
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="items")
    basket = relationship("Basket")

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id!r} basket={self.basket_id!r}>"
