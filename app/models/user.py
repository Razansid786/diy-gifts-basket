
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="UUID primary key.",
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        doc="Unique email address used for login.",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False,
        doc="Bcrypt-hashed password.",
    )

    full_name: Mapped[str] = mapped_column(
        String(150), nullable=False, default="",
        doc="User's display name.",
    )
    phone_number: Mapped[str] = mapped_column(
        String(50), nullable=True,
        doc="User's phone number.",
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="customer",
        doc="Authorization role: 'customer' or 'admin'.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="Soft-delete flag; inactive users cannot log in.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Row creation time (UTC).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        doc="Last modification time (UTC).",
    )

    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    baskets = relationship("Basket", back_populates="user")
    carts = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r} role={self.role!r}>"