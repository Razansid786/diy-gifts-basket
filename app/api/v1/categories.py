"""
app/api/v1/categories.py
────────────────────────
Product category endpoints (FR7).

Routes:
    GET /categories      — List all categories.
    GET /categories/{id} — Get a single category by ID.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.category import CategoryResponse
from app.services.category_service import CategoryService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "/",
    response_model=List[CategoryResponse],
    summary="List all product categories (FR7)",
)
async def list_categories(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Return all product categories, paginated."""
    service = CategoryService(db)
    return await service.list_categories(
        skip=pagination.skip, limit=pagination.limit
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category by ID",
)
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return a single category by its ID."""
    service = CategoryService(db)
    return await service.get_category(category_id)
