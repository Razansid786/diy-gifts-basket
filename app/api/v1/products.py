"""
app/api/v1/products.py
──────────────────────
Product catalog endpoints (FR6–FR10).

Routes:
    GET /products          — List products (paginated).
    GET /products/search   — Search products with filters (FR8).
    GET /products/{id}     — Get a single product (FR6).
    GET /products/{id}/related — Get related items (FR9).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.product import ProductResponse
from app.services.product_service import ProductService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List all products (FR6)",
)
async def list_products(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Return all active products, paginated."""
    service = ProductService(db)
    return await service.list_products(
        skip=pagination.skip, limit=pagination.limit
    )


@router.get(
    "/search",
    response_model=List[ProductResponse],
    summary="Search products (FR8)",
)
async def search_products(
    q: Optional[str] = Query(None, description="Keyword search term."),
    category_id: Optional[str] = Query(None, description="Filter by category."),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock_only: bool = Query(False, description="Exclude sold-out items."),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Search products by keyword and optional filters.

    Matches against title and description (case-insensitive).
    """
    service = ProductService(db)
    return await service.search_products(
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID (FR6)",
)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return a single product with its details and sold-out status."""
    service = ProductService(db)
    return await service.get_product(product_id)


@router.get(
    "/{product_id}/related",
    response_model=List[ProductResponse],
    summary="Get related items (FR9)",
)
async def get_related_products(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return products related to the given product for cross-selling."""
    service = ProductService(db)
    return await service.get_related_products(product_id)
