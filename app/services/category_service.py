"""
app/services/category_service.py
────────────────────────────────
Business logic for product categories (FR7).
"""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.repositories.category_repo import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """CRUD operations for product categories."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.category_repo = CategoryRepository(db)

    async def list_categories(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """Return all categories, paginated."""
        return await self.category_repo.get_all(skip=skip, limit=limit)

    async def get_category(self, category_id: str) -> Category:
        """Get a single category by ID."""
        cat = await self.category_repo.get_by_id(category_id)
        if not cat:
            raise NotFoundError("Category", category_id)
        return cat

    async def create_category(self, data: CategoryCreate) -> Category:
        """
        Create a new category.

        Raises ``ConflictError`` if the slug already exists.
        """
        existing = await self.category_repo.get_by_slug(data.slug)
        if existing:
            raise ConflictError(f"Category with slug '{data.slug}' already exists.")
        return await self.category_repo.create(data.model_dump())

    async def update_category(self, category_id: str, data: CategoryUpdate) -> Category:
        """Update a category's fields."""
        cat = await self.category_repo.update(
            category_id, data.model_dump(exclude_unset=True)
        )
        if not cat:
            raise NotFoundError("Category", category_id)
        return cat

    async def delete_category(self, category_id: str) -> bool:
        """Delete a category by ID."""
        if not await self.category_repo.delete(category_id):
            raise NotFoundError("Category", category_id)
        return True
