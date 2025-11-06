from datetime import datetime
from typing import List, Optional
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus as ModelOrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate


async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
    """
    Получает один заказ по его ID.
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.product))
        .filter(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def get_orders_by_product(
    db: AsyncSession,
    product_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Order]:
    """
    Получает список заказов для конкретного продукта с пагинацией.
    """
    stmt = (
        select(Order)
        .filter(Order.product_id == product_id)
        .offset(skip)
        .limit(limit)
        .order_by(Order.order_date.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_orders_by_buyer(
    db: AsyncSession,
    buyer_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Order]:
    """
    Получает список заказов конкретного покупателя с пагинацией.
    """
    stmt = (
        select(Order)
        .filter(Order.buyer_id == buyer_id)
        .offset(skip)
        .limit(limit)
        .order_by(Order.order_date.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_orders_by_seller(
    db: AsyncSession,
    seller_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Order]:
    """
    Получает список заказов для продуктов конкретного продавца с пагинацией.
    """
    stmt = (
        select(Order)
        .join(Product)
        .filter(Product.seller_id == seller_id)
        .offset(skip)
        .limit(limit)
        .order_by(Order.order_date.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_order(
    db: AsyncSession,
    order_data: OrderCreate,
    buyer_id: int
) -> Optional[Order]:
    """
    Создает новый заказ.
    
    Returns:
        Созданный объект Order или None, если продукт не найден или недостаточно товара на складе
    """
    # Получаем продукт
    product_stmt = select(Product).where(Product.id == order_data.product_id)
    product_result = await db.execute(product_stmt)
    product = product_result.scalar_one_or_none()
    
    if not product:
        return None
    
    # Проверяем наличие товара на складе
    if product.stock < order_data.quantity:
        return None
    
    # Вычисляем общую стоимость
    total_price = product.price * order_data.quantity
    
    try:
        new_order = Order(
            product_id=order_data.product_id,
            buyer_id=buyer_id,
            quantity=order_data.quantity,
            total_price=total_price,
            message=order_data.message,
            status=ModelOrderStatus.PENDING.value
        )
        db.add(new_order)
        
        # Уменьшаем количество товара на складе
        product.stock -= order_data.quantity
        
        await db.commit()
        await db.refresh(new_order)
        return new_order
    except IntegrityError:
        await db.rollback()
        return None
    except SQLAlchemyError as e:
        await db.rollback()
        raise ValueError(f"Database error: {str(e)}")


async def update_order(
    db: AsyncSession,
    order_id: int,
    update_data: OrderUpdate
) -> Optional[Order]:
    """
    Обновляет существующий заказ.
    
    Returns:
        Обновленный объект Order или None, если заказ не найден
    """
    order = await get_order_by_id(db, order_id)
    if not order:
        return None

    update_values = update_data.model_dump(exclude_unset=True)
    for field, value in update_values.items():
        if value is not None:
            # Для enum-полей сохраняем значение (не сам enum)
            setattr(order, field, value.value if isinstance(value, Enum) else value)

    try:
        await db.commit()
        await db.refresh(order)
        return order
    except SQLAlchemyError:
        await db.rollback()
        raise


async def delete_order(db: AsyncSession, order_id: int) -> bool:
    """
    Удаляет заказ из базы данных.
    
    Returns:
        True, если удаление прошло успешно, False, если заказ не найден
    """
    order = await get_order_by_id(db, order_id)
    if not order:
        return False

    # Возвращаем товар на склад при удалении заказа
    if order.status == ModelOrderStatus.PENDING.value or order.status == ModelOrderStatus.CONFIRMED.value:
        product_stmt = select(Product).where(Product.id == order.product_id)
        product_result = await db.execute(product_stmt)
        product = product_result.scalar_one_or_none()
        if product:
            product.stock += order.quantity

    await db.delete(order)
    await db.commit()
    return True


async def get_orders_by_status(
    db: AsyncSession,
    status: ModelOrderStatus,
    skip: int = 0,
    limit: int = 100
) -> List[Order]:
    """
    Получает заказы по указанному статусу с пагинацией.
    """
    stmt = (
        select(Order)
        .filter(Order.status == status.value)
        .offset(skip)
        .limit(limit)
        .order_by(Order.order_date.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def change_order_status(
    db: AsyncSession,
    order_id: int,
    new_status: ModelOrderStatus
) -> Optional[Order]:
    """
    Изменяет статус заказа.
    """
    order = await get_order_by_id(db, order_id)
    if not order:
        return None

    order.status = new_status.value

    await db.commit()
    await db.refresh(order)
    return order

