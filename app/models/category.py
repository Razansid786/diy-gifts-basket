
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
        doc="Display name (e.g. 'Snacks').",
    )
    slug: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False,
        doc="URL-friendly slug (e.g. 'snacks').",
    )
    description: Mapped[str] = mapped_column(
        String(500), nullable=True, default="",
    )
    image_url: Mapped[str] = mapped_column(
        String(500), nullable=True, default="",
        doc="Optional category banner image.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    products = relationship("Product", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category id={self.id!r} name={self.name!r}>"