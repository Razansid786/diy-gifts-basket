"""
app/models/user.py
──────────────────
ORM model for the ``users`` table.

Stores registered customer and admin accounts.  Guests do *not*
have a row here — they are identified by ``session_id`` on other
tables (baskets, carts).

Columns
~~~~~~~
* ``id``             — UUID primary key (auto-generated).
* ``email``          — Unique, indexed for fast login lookup.
* ``hashed_password``— Bcrypt hash; never stored as plain text.
* ``full_name``      — Display name.
* ``role``           — Either ``"customer"`` or ``"admin"``.
* ``is_active``      — Soft-delete flag.
* ``created_at``     — Row creation timestamp (UTC).
* ``updated_at``     — Last modification timestamp (UTC).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # ── Primary key ──────────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="UUID primary key.",
    )

    # ── Credentials ──────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        doc="Unique email address used for login.",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False,
        doc="Bcrypt-hashed password.",
    )

    # ── Profile ──────────────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(
        String(150), nullable=False, default="",
        doc="User's display name.",
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="customer",
        doc="Authorization role: 'customer' or 'admin'.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="Soft-delete flag; inactive users cannot log in.",
    )

    # ── Timestamps ───────────────────────────────────────────────────
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

    # ── Relationships ────────────────────────────────────────────────
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    baskets = relationship("Basket", back_populates="user")
    carts = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r} role={self.role!r}>"
