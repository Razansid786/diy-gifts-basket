
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.cart import Cart, CartItem
from app.repositories.basket_repo import BasketRepository
from app.repositories.cart_repo import CartRepository, CartItemRepository
from app.schemas.cart import CartItemAdd, CartItemUpdate

SHIPPING_TIERS = [
    (0,     50,   9.99),
    (50,    100,  5.99),
    (100,   None, 0.00),
]

def calculate_shipping_fee(subtotal: float) -> float:

    for low, high, fee in SHIPPING_TIERS:
        if high is None and subtotal >= low:
            return fee
        if high is not None and low <= subtotal < high:
            return fee
    return 9.99

class CartService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.cart_item_repo = CartItemRepository(db)
        self.basket_repo = BasketRepository(db)

    async def get_cart(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> dict:

        cart = await self.cart_repo.get_or_create(
            user_id=user_id, session_id=session_id
        )

        subtotal = await self.cart_repo.calculate_subtotal(cart.id)
        shipping_fee = calculate_shipping_fee(subtotal)

        return {
            "cart": cart,
            "subtotal": round(subtotal, 2),
            "shipping_fee": round(shipping_fee, 2),
            "total": round(subtotal + shipping_fee, 2),
        }

    async def add_item(
        self,
        data: CartItemAdd,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:

        basket = await self.basket_repo.get_with_base(data.basket_id)
        if not basket:
            raise NotFoundError("Basket", data.basket_id)
        if basket.status != "complete":
            raise ValidationError("Only completed baskets can be added to the cart.")

        cart = await self.cart_repo.get_or_create(
            user_id=user_id, session_id=session_id
        )

        await self.cart_item_repo.create({
            "cart_id": cart.id,
            "basket_id": data.basket_id,
            "quantity": data.quantity,
        })

        subtotal = await self.cart_repo.calculate_subtotal(cart.id)
        shipping_fee = calculate_shipping_fee(subtotal)

        if user_id:
            cart = await self.cart_repo.get_by_user(user_id)
        elif session_id:
            cart = await self.cart_repo.get_by_session(session_id)

        return {
            "cart": cart,
            "subtotal": round(subtotal, 2),
            "shipping_fee": round(shipping_fee, 2),
            "total": round(subtotal + shipping_fee, 2),
        }

    async def update_item(
        self,
        item_id: str,
        data: CartItemUpdate,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:

        item = await self.cart_item_repo.get_by_id(item_id)
        if not item:
            raise NotFoundError("CartItem", item_id)

        await self.cart_item_repo.update(item_id, {"quantity": data.quantity})
        return await self.get_cart(user_id=user_id, session_id=session_id)

    async def remove_item(
        self,
        item_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:

        if not await self.cart_item_repo.delete(item_id):
            raise NotFoundError("CartItem", item_id)
        return await self.get_cart(user_id=user_id, session_id=session_id)

    async def _calculate_subtotal(self, cart: Cart) -> float:

        return await self.cart_repo.calculate_subtotal(cart.id)