
import json
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.order import Order, OrderItem
from app.repositories.basket_repo import BasketRepository
from app.repositories.cart_repo import CartRepository, CartItemRepository
from app.repositories.order_repo import OrderRepository, OrderItemRepository
from app.repositories.address_repo import AddressRepository
from app.schemas.order import CheckoutRequest, OrderStatusUpdate, PackingListItem, PackingListResponse
from app.services.cart_service import CartService
from app.utils.email import send_order_confirmation

class OrderService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.order_item_repo = OrderItemRepository(db)
        self.cart_repo = CartRepository(db)
        self.cart_item_repo = CartItemRepository(db)
        self.basket_repo = BasketRepository(db)
        self.address_repo = AddressRepository(db)
        self.cart_service = CartService(db)

    async def checkout(
        self,
        data: CheckoutRequest,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Order:

        shipping_json = await self._resolve_shipping(data, user_id)

        cart_data = await self.cart_service.get_cart(
            user_id=user_id, session_id=session_id
        )
        cart = cart_data["cart"]

        if not cart.items:
            raise ValidationError("Cart is empty. Add baskets before checkout.")

        subtotal = cart_data["subtotal"]
        shipping_fee = cart_data["shipping_fee"]
        total = cart_data["total"]

        payment_ref = f"PAY-{uuid.uuid4().hex[:12].upper()}"

        existing = await self.order_repo.get_by_payment_ref(payment_ref)
        if existing:
            return existing

        order = await self.order_repo.create({
            "user_id": user_id,
            "guest_email": data.guest_email,
            "shipping_address_json": shipping_json,
            "shipping_fee": shipping_fee,
            "subtotal": subtotal,
            "total": total,
            "status": "pending",
            "payment_ref": payment_ref,
        })

        basket_ids = [item.basket_id for item in cart.items]
        basket_totals = await self.basket_repo.get_totals_by_ids(basket_ids)

        order_items_payload = []
        for cart_item in cart.items:
            basket_total = basket_totals.get(cart_item.basket_id)
            if basket_total is None:
                continue

            order_items_payload.append({
                "order_id": order.id,
                "basket_id": cart_item.basket_id,
                "unit_price": basket_total,
                "quantity": cart_item.quantity,
            })

        await self.order_item_repo.create_many(order_items_payload)

        await self.cart_item_repo.clear_cart(cart.id)

        recipient = data.guest_email if data.guest_email else None
        if user_id:
            from app.repositories.user_repo import UserRepository
            user_repo = UserRepository(self.db)
            user = await user_repo.get_by_id(user_id)
            if user:
                recipient = user.email

        if recipient:
            await send_order_confirmation(recipient, order)

        return await self.order_repo.get_with_items(order.id)

    async def get_user_orders(self, user_id: str) -> List[Order]:

        return await self.order_repo.get_user_orders(user_id)

    async def get_order(self, order_id: str) -> Order:

        order = await self.order_repo.get_with_items(order_id)
        if not order:
            raise NotFoundError("Order", order_id)
        return order

    async def list_all_orders(self, skip: int = 0, limit: int = 50) -> List[Order]:

        return await self.order_repo.get_all_sorted(skip=skip, limit=limit)

    async def update_order_status(
        self, order_id: str, data: OrderStatusUpdate
    ) -> Order:

        valid_statuses = {"pending", "processing", "shipped", "delivered"}
        if data.status not in valid_statuses:
            raise ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        order = await self.order_repo.update(order_id, {"status": data.status})
        if not order:
            raise NotFoundError("Order", order_id)
        return await self.order_repo.get_with_items(order_id)

    async def get_packing_list(self, order_id: str) -> List[PackingListResponse]:

        order = await self.order_repo.get_with_items(order_id)
        if not order:
            raise NotFoundError("Order", order_id)

        packing_lists = []
        basket_ids = [item.basket_id for item in order.items if item.basket_id]
        baskets = await self.basket_repo.get_many_with_items(basket_ids)
        baskets_by_id = {basket.id: basket for basket in baskets}

        for order_item in order.items:
            basket = baskets_by_id.get(order_item.basket_id)
            if not basket:
                continue

            items = [
                PackingListItem(
                    product_id=bi.product.id,
                    product_title=bi.product.title,
                    product_sku=bi.product.sku,
                    quantity=bi.quantity,
                )
                for bi in basket.items
                if bi.product
            ]

            pers = basket.personalization
            packing_lists.append(PackingListResponse(
                order_id=order.id,
                basket_id=basket.id,
                base_name=basket.base.name if basket.base else "N/A",
                base_size=basket.base.size if basket.base else "N/A",
                items=items,
                personalization_message=pers.gift_message if pers else None,
                ribbon_color=pers.ribbon_color if pers else None,
                gift_tag_image_url=pers.gift_tag_image_url if pers else None,
                requested_delivery_date=str(pers.requested_delivery_date) if pers and pers.requested_delivery_date else None,
            ))

        return packing_lists

    async def _resolve_shipping(
        self, data: CheckoutRequest, user_id: Optional[str]
    ) -> str:

        if data.address_id and user_id:
            address = await self.address_repo.get_by_id(data.address_id)
            if not address or address.user_id != user_id:
                raise NotFoundError("Address", data.address_id)
            return json.dumps({
                "line1": address.line1,
                "line2": address.line2 or "",
                "city": address.city,
                "state": address.state,
                "zip_code": address.zip_code,
                "country": address.country,
            })

        return json.dumps(data.shipping.model_dump())
