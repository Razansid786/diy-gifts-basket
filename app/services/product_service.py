
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate

class ProductService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)

    async def list_products(
        self, skip: int = 0, limit: int = 50
    ) -> List[Product]:

        return await self.product_repo.get_all(skip=skip, limit=limit)

    async def get_product(self, product_id: str) -> Product:

        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product", product_id)
        return product

    async def search_products(
        self,
        q: Optional[str] = None,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Product]:

        return await self.product_repo.search(
            q=q,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            skip=skip,
            limit=limit,
        )

    async def get_related_products(self, product_id: str) -> List[Product]:

        await self.get_product(product_id)
        return await self.product_repo.get_related(product_id)

    async def create_product(self, data: ProductCreate) -> Product:

        existing = await self.product_repo.search(q=data.sku, limit=1)
        for p in existing:
            if p.sku == data.sku:
                raise ConflictError(f"Product with SKU '{data.sku}' already exists.")

        return await self.product_repo.create(data.model_dump())

    async def update_product(self, product_id: str, data: ProductUpdate) -> Product:

        product = await self.product_repo.update(
            product_id, data.model_dump(exclude_unset=True)
        )
        if not product:
            raise NotFoundError("Product", product_id)
        return product