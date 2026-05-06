
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

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True, unique=True,
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

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
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="items")
    basket = relationship("Basket")

    def __repr__(self) -> str:
        return f"<CartItem cart={self.cart_id!r} basket={self.basket_id!r} qty={self.quantity}>"
