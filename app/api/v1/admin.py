
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

    service = ProductService(db)
    return await service.update_product(product_id, data)

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

    service = CategoryService(db)
    return await service.update_category(category_id, data)

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

    service = BasketService(db)
    return await service.create_base(data.model_dump())

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

    service = OrderService(db)
    return await service.update_order_status(order_id, data)