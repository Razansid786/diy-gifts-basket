"""
app/repositories/product_repo.py
────────────────────────────────
Data-access layer for the ``products`` table (FR6–FR10).

Contains custom queries for:
* Searching by keyword (FR8)
* Filtering by category (FR7)
* Fetching related items (FR9)
"""

from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductRelation
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for product catalog queries."""

    model = Product

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def search(
        self,
        q: Optional[str] = None,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Product]:
        """
        Full-text keyword search with optional filters (FR8).

        Parameters
        ----------
        q : str, optional
            Search term matched against title and description (case-insensitive).
        category_id : str, optional
            Filter by category FK.
        min_price / max_price : float, optional
            Price range filter.
        in_stock_only : bool
            If True, exclude items with ``inventory_count <= 0``.
        """
        stmt = select(Product).where(Product.is_active.is_(True))

        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Product.title.ilike(pattern),
                    Product.description.ilike(pattern),
                )
            )

        if category_id:
            stmt = stmt.where(Product.category_id == category_id)

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        if in_stock_only:
            stmt = stmt.where(Product.inventory_count > 0)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_category(
        self, category_id: str, skip: int = 0, limit: int = 50
    ) -> List[Product]:
        """Return all active products in a given category (FR7)."""
        result = await self.db.execute(
            select(Product)
            .where(Product.category_id == category_id, Product.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_related(self, product_id: str) -> List[Product]:
        """
        Return products linked via ``product_relations`` (FR9).

        Uses a sub-query on the association table to find related IDs,
        then fetches the full product rows.
        """
        # Find related product IDs
        sub = select(ProductRelation.related_product_id).where(
            ProductRelation.product_id == product_id
        )
        result = await self.db.execute(
            select(Product).where(Product.id.in_(sub), Product.is_active.is_(True))
        )
        return list(result.scalars().all())
