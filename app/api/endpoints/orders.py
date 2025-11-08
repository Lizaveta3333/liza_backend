from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.models.order import OrderStatus as ModelOrderStatus
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderStatus
)
from app.crud.order import (
    get_order_by_id,
    get_orders_by_product,
    get_orders_by_buyer,
    get_orders_by_seller,
    create_order,
    update_order,
    delete_order,
    get_orders_by_status,
    change_order_status
)
from app.services.kafka_service import send_order_event, get_kafka_status

router = APIRouter()


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый заказ",
    description="Создает новый заказ на продукт. Требуется аутентификация."
)
async def create_new_order(
    order_data: OrderCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Создает новый заказ на продукт.
    
    Параметры:
    - order_data: Данные для создания заказа (тело запроса)
    - current_user: Текущий аутентифицированный пользователь (автоматически)
    
    Возвращает:
    - Созданный заказ или ошибку 400, если продукт не найден или недостаточно товара
    """
    order = await create_order(
        db=db,
        order_data=order_data,
        buyer_id=current_user.id
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found or insufficient stock"
        )
    
    # Send order creation event to Kafka
    order_dict = {
        "id": order.id,
        "buyer_id": order.buyer_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": order.status,
        "created_at": order.order_date.isoformat() if order.order_date else None,
    }
    send_order_event("order_created", order_dict)
    
    return order


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Получить заказ по ID",
    description="Возвращает полную информацию о заказе по его ID."
)
async def read_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получает информацию о заказе по его ID.
    
    Параметры:
    - order_id: ID заказа (из URL)
    
    Возвращает:
    - Объект заказа или ошибку 404, если не найден
    """
    order = await get_order_by_id(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="Список всех заказов",
    description="Возвращает список всех заказов с пагинацией. Требуется аутентификация."
)
async def read_orders(
    current_user: UserResponse = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит на количество записей"),
    db: AsyncSession = Depends(get_db)
):
    """Возвращает список всех заказов текущего пользователя с пагинацией"""
    return await get_orders_by_buyer(db, buyer_id=current_user.id, skip=skip, limit=limit)


@router.get(
    "/product/{product_id}",
    response_model=List[OrderResponse],
    summary="Получить заказы по продукту",
    description="Возвращает список заказов для указанного продукта с пагинацией."
)
async def read_orders_by_product(
    product_id: int,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит на количество записей"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает список заказов для конкретного продукта.
    
    Параметры:
    - product_id: ID продукта (из URL)
    - skip: Смещение для пагинации (query параметр)
    - limit: Лимит записей (query параметр)
    
    Возвращает:
    - Список заказов (может быть пустым)
    """
    return await get_orders_by_product(
        db=db,
        product_id=product_id,
        skip=skip,
        limit=limit
    )


@router.get(
    "/my/",
    response_model=List[OrderResponse],
    summary="Мои заказы",
    description="Возвращает список заказов текущего аутентифицированного пользователя."
)
async def read_my_orders(
    current_user: UserResponse = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит на количество записей"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает заказы текущего пользователя.
    
    Параметры:
    - current_user: Текущий пользователь (автоматически)
    - skip: Смещение для пагинации
    - limit: Лимит записей
    
    Возвращает:
    - Список заказов пользователя
    """
    return await get_orders_by_buyer(
        db=db,
        buyer_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.get(
    "/my/sales/",
    response_model=List[OrderResponse],
    summary="Заказы на мои продукты",
    description="Возвращает список заказов на продукты текущего пользователя (продавца)."
)
async def read_orders_for_my_products(
    current_user: UserResponse = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит на количество записей"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает заказы на продукты текущего пользователя (как продавца).
    
    Параметры:
    - current_user: Текущий пользователь (автоматически)
    - skip: Смещение для пагинации
    - limit: Лимит записей
    
    Возвращает:
    - Список заказов на продукты пользователя
    """
    return await get_orders_by_seller(
        db=db,
        seller_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.get(
    "/status/{status}",
    response_model=List[OrderResponse],
    summary="Получить заказы по статусу",
    description="Возвращает список заказов с указанным статусом с пагинацией."
)
async def read_orders_by_status(
    status: OrderStatus,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит на количество записей"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает заказы по указанному статусу.
    
    Параметры:
    - status: Статус заказа (из URL)
    - skip: Смещение для пагинации
    - limit: Лимит записей
    
    Возвращает:
    - Список заказов с указанным статусом
    """
    return await get_orders_by_status(
        db=db,
        status=ModelOrderStatus[status.name],
        skip=skip,
        limit=limit
    )


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Обновить заказ",
    description="Обновляет данные существующего заказа. Только владелец заказа или продавец могут его изменить."
)
async def update_existing_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновляет данные заказа.
    
    Параметры:
    - order_id: ID заказа (из URL)
    - order_data: Данные для обновления (тело запроса)
    - current_user: Текущий пользователь (для проверки прав)
    
    Возвращает:
    - Обновленный заказ или ошибку 404/403
    """
    existing_order = await get_order_by_id(db, order_id=order_id)
    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Проверяем права: покупатель или продавец продукта
    from app.crud.product import get_product_by_id
    product = await get_product_by_id(db, existing_order.product_id)
    
    if existing_order.buyer_id != current_user.id and (not product or product.seller_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this order"
        )

    updated_order = await update_order(
        db=db,
        order_id=order_id,
        update_data=order_data
    )
    return updated_order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить заказ",
    description="Удаляет заказ. Только владелец заказа может его удалить."
)
async def delete_existing_order(
    order_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаляет заказ.
    
    Параметры:
    - order_id: ID заказа (из URL)
    - current_user: Текущий пользователь (для проверки прав)
    
    Возвращает:
    - 204 No Content при успехе или ошибку 404/403
    """
    existing_order = await get_order_by_id(db, order_id=order_id)
    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if existing_order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this order"
        )

    success = await delete_order(db, order_id=order_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting order"
        )
    return JSONResponse(content=None, status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Изменить статус заказа",
    description="Изменяет статус заказа. Только продавец продукта может изменить статус."
)
async def change_order_status_endpoint(
    order_id: int,
    new_status: OrderStatus,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Изменяет статус заказа.
    
    Параметры:
    - order_id: ID заказа (из URL)
    - new_status: Новый статус (тело запроса)
    - current_user: Текущий пользователь (для проверки прав)
    
    Возвращает:
    - Обновленный заказ или ошибку 404/403
    """
    existing_order = await get_order_by_id(db, order_id=order_id)
    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Проверяем права: только продавец продукта может изменить статус
    from app.crud.product import get_product_by_id
    product = await get_product_by_id(db, existing_order.product_id)
    
    if not product or product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only product seller can change order status"
        )

    updated = await change_order_status(
        db=db,
        order_id=order_id,
        new_status=ModelOrderStatus[new_status.name]
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status change"
        )
    
    # Send order status change event to Kafka
    order_dict = {
        "id": updated.id,
        "buyer_id": updated.buyer_id,
        "product_id": updated.product_id,
        "quantity": updated.quantity,
        "status": updated.status,
        "created_at": updated.order_date.isoformat() if updated.order_date else None,
    }
    send_order_event("order_status_changed", order_dict)
    
    return updated


@router.get(
    "/test/kafka",
    summary="Test Kafka connection",
    description="Tests if Kafka is working and returns connection status"
)
async def test_kafka():
    """
    Tests Kafka connection and sends a test message.
    Returns status information about Kafka producer and consumer.
    """
    status = get_kafka_status()
    return status
