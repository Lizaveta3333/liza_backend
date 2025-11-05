from fastapi import APIRouter
from app.api.endpoints import auth, users, orders, product

router = APIRouter(prefix="/api")

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(orders.router, prefix="/orders", tags=["Orders"])
router.include_router(product.router, prefix="/products", tags=["Products"]) 
