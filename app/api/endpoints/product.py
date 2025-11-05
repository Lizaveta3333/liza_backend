from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductStatus
)
from app.crud.product import (
    get_product_by_id,
    get_products_by_seller,
    get_products_by_category,
    create_product,
    update_product,
    delete_product,
    get_all_products,
    get_recent_products,
    change_product_status
)

router = APIRouter()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый продукт"
)
async def create_new_product(
    product_data: ProductCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """
    Создает продукт для текущего пользователя.
    - Требуется аутентификация
    - Устанавливает статус ACTIVE по умолчанию
    """
    try:
        return await create_product(db, product_data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Получить продукт по ID"
)
async def read_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Возвращает полные данные продукта по его ID"""
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="Список всех продуктов"
)
async def read_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[ProductStatus] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> List[ProductResponse]:
    """Возвращает список продуктов с пагинацией"""
    return await get_all_products(db, skip=skip, limit=limit, status_filter=status_filter)


@router.get(
    "/category/{category}",
    response_model=List[ProductResponse],
    summary="Получить продукты по категории"
)
async def read_products_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> List[ProductResponse]:
    """Возвращает список продуктов указанной категории"""
    return await get_products_by_category(db, category, skip=skip, limit=limit)


@router.get(
    "/my/",
    response_model=List[ProductResponse],
    summary="Мои продукты"
)
async def read_my_products(
    current_user: UserResponse = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> List[ProductResponse]:
    """Возвращает продукты текущего пользователя"""
    return await get_products_by_seller(db, current_user.id, skip, limit)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Обновить продукт"
)
async def update_existing_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """
    Обновляет данные продукта.
    - Только для владельца продукта
    - Можно обновлять отдельные поля
    """
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your product")

    updated = await update_product(db, product_id, product_data)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")
    return updated


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить продукт"
)
async def delete_existing_product(
    product_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаляет продукт.
    - Только для владельца продукта
    """
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your product")

    success = await delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=500, detail="Delete failed")
    return None


@router.patch(
    "/{product_id}/status",
    response_model=ProductResponse,
    summary="Изменить статус продукта"
)
async def change_status(
    product_id: int,
    new_status: ProductStatus,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Изменяет статус продукта (только для владельца)"""
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your product")

    updated = await change_product_status(db, product_id, new_status)
    if not updated:
        raise HTTPException(status_code=400, detail="Invalid status change")
    return updated

