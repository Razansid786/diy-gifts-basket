
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Numeric, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class ProductRelation(Base):

    __tablename__ = "product_relations"

    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    related_product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    sku: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False,
        doc="Stock Keeping Unit — unique product identifier.",
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False,
        doc="Product display name.",
    )
    description: Mapped[str] = mapped_column(
        String(1000), nullable=True, default="",
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Unit price in USD.",
    )
    image_url: Mapped[str] = mapped_column(
        String(500), nullable=True, default="",
    )

    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    inventory_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        doc="Current stock level; 0 = sold out (FR10).",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="Soft-delete / visibility toggle.",
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

    category = relationship("Category", back_populates="products")

    related_products = relationship(
        "Product",
        secondary="product_relations",
        primaryjoin="Product.id == ProductRelation.product_id",
        secondaryjoin="Product.id == ProductRelation.related_product_id",
        lazy="raise",
    )

    @property
    def is_sold_out(self) -> bool:

        return self.inventory_count <= 0

    def __repr__(self) -> str:
        return f"<Product id={self.id!r} sku={self.sku!r} title={self.title!r}>"