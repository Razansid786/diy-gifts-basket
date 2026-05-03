from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.addresses import router as addresses_router
from app.api.v1.categories import router as categories_router
from app.api.v1.products import router as products_router
from app.api.v1.baskets import router as baskets_router
from app.api.v1.personalization import router as personalization_router
from app.api.v1.cart import router as cart_router
from app.api.v1.orders import router as orders_router
from app.api.v1.admin import router as admin_router
from app.api.v1.images import router as images_router
from app.api.v1.chat import router as chat_router
from app.api.v1.ai import router as ai_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(addresses_router)
v1_router.include_router(categories_router)
v1_router.include_router(products_router)
v1_router.include_router(baskets_router)
v1_router.include_router(personalization_router)
v1_router.include_router(cart_router)
v1_router.include_router(orders_router)
v1_router.include_router(admin_router)
v1_router.include_router(images_router)
v1_router.include_router(chat_router)
v1_router.include_router(ai_router)