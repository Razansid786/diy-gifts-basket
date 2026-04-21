"""
app/api/v1/admin.py
───────────────────
Admin panel endpoints (FR27–FR30).

All endpoints require the ``admin`` role.

Routes:
    POST /admin/products               — Add a new product (FR27).
    PUT  /admin/products/{id}          — Edit a product (FR27).
    POST /admin/categories             — Add a new category.
    PUT  /admin/categories/{id}        — Edit a category.
    POST /admin/bases                  — Add a new gift base.
    GET  /admin/orders                 — List all orders (FR28).
    GET  /admin/orders/{id}/packing-list — View packing list (FR29).
    PUT  /admin/orders/{id}/status     — Update order status (FR30).
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin
from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.order import OrderResponse, OrderStatusUpdate, PackingListResponse
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.basket import GiftBaseCreate, GiftBaseResponse
from app.services.basket_service import BasketService
from app.services.category_service import CategoryService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Products (FR27) ─────────────────────────────────────────────────

@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=201,
    summary="Add a new product (FR27)",
    dependencies=[Depends(require_admin)],
)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Admin: add a new product to the catalog."""
    service = ProductService(db)
    return await service.create_product(data)


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Edit a product (FR27)",
    dependencies=[Depends(require_admin)],
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Admin: update product fields (title, price, inventory, etc.)."""
    service = ProductService(db)
    return await service.update_product(product_id, data)


# ── Categories ───────────────────────────────────────────────────────

@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=201,
    summary="Add a new category",
    dependencies=[Depends(require_admin)],
)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Admin: add a new product category."""
    service = CategoryService(db)
    return await service.create_category(data)


@router.put(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Edit a category",
    dependencies=[Depends(require_admin)],
)
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Admin: update category name, slug, description, or image."""
    service = CategoryService(db)
    return await service.update_category(category_id, data)


# ── Gift Bases ───────────────────────────────────────────────────────

@router.post(
    "/bases",
    response_model=GiftBaseResponse,
    status_code=201,
    summary="Add a new gift base / container",
    dependencies=[Depends(require_admin)],
)
async def create_base(
    data: GiftBaseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Admin: add a new gift base type (e.g. Basket, Box, Tin)."""
    service = BasketService(db)
    return await service.create_base(data.model_dump())


# ── Orders (FR28, FR29, FR30) ────────────────────────────────────────

@router.get(
    "/orders",
    response_model=List[OrderResponse],
    summary="List all orders sorted by date (FR28)",
    dependencies=[Depends(require_admin)],
)
async def list_all_orders(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Admin: return all orders, newest first."""
    service = OrderService(db)
    return await service.list_all_orders(
        skip=pagination.skip, limit=pagination.limit
    )


@router.get(
    "/orders/{order_id}/packing-list",
    response_model=List[PackingListResponse],
    summary="View packing list for a basket order (FR29)",
    dependencies=[Depends(require_admin)],
)
async def get_packing_list(
    order_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Admin: generate a detailed packing list for an order.

    Returns one packing list per basket in the order, including
    the container, items, and personalization details.
    """
    service = OrderService(db)
    return await service.get_packing_list(order_id)


@router.put(
    "/orders/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status (FR30)",
    dependencies=[Depends(require_admin)],
)
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Admin: change order status (pending → processing → shipped → delivered)."""
    service = OrderService(db)
    return await service.update_order_status(order_id, data)
