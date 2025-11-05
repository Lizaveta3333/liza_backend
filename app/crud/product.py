from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductStatus


async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    """
    Получает продукт по ID. Возвращает None если не найден.
    """
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_products_by_seller(
    db: AsyncSession,
    seller_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Product]:
    """
    Получает продукты конкретного продавца с пагинацией.
    """
    stmt = (
        select(Product)
        .where(Product.seller_id == seller_id)
        .order_by(Product.time_posted.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_products_by_category(
    db: AsyncSession,
    category: str,
    skip: int = 0,
    limit: int = 100
) -> List[Product]:
    """
    Получает продукты по категории с пагинацией.
    """
    stmt = (
        select(Product)
        .where(Product.category == category)
        .where(Product.status == ProductStatus.ACTIVE.value)
        .order_by(Product.time_posted.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_product(
    db: AsyncSession,
    product_data: ProductCreate,
    seller_id: int
) -> Product:
    """
    Создает новый продукт с привязкой к продавцу.
    Автоматически устанавливает time_posted и статус.
    """
    try:
        product_dict = product_data.model_dump(exclude_unset=True)
        
        # Convert Enum values to strings
        if 'status' in product_dict and isinstance(product_dict['status'], Enum):
            product_dict['status'] = product_dict['status'].value
        
        new_product = Product(
            **product_dict,
            seller_id=seller_id
        )
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        return new_product
    except SQLAlchemyError as e:
        await db.rollback()
        raise ValueError(f"Database error: {str(e)}")


async def update_product(
    db: AsyncSession,
    product_id: int,
    update_data: ProductUpdate
) -> Optional[Product]:
    """
    Обновляет данные продукта. Возвращает обновленный объект или None если не найден.
    """
    product = await get_product_by_id(db, product_id)
    if not product:
        return None

    update_values = update_data.model_dump(exclude_unset=True)
    for field, value in update_values.items():
        if value is not None:
            if isinstance(value, Enum):
                setattr(product, field, value.value)
            else:
                setattr(product, field, value)

    try:
        await db.commit()
        await db.refresh(product)
        return product
    except SQLAlchemyError:
        await db.rollback()
        raise


async def delete_product(db: AsyncSession, product_id: int) -> bool:
    """
    Удаляет продукт по ID. Возвращает True если успешно, False если не найден.
    """
    product = await get_product_by_id(db, product_id)
    if not product:
        return False

    await db.delete(product)
    await db.commit()
    return True


async def get_all_products(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[ProductStatus] = None
) -> List[Product]:
    """
    Получает список всех продуктов с пагинацией.
    Сортировка по дате создания (новые сначала).
    """
    stmt = select(Product)
    
    if status_filter:
        stmt = stmt.where(Product.status == status_filter.value)
    
    stmt = (
        stmt
        .order_by(Product.time_posted.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_recent_products(
    db: AsyncSession,
    hours: int = 24,
    limit: int = 10
) -> List[Product]:
    """
    Получает свежие продукты за указанный период.
    """
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    stmt = (
        select(Product)
        .where(Product.time_posted >= time_threshold)
        .where(Product.status == ProductStatus.ACTIVE.value)
        .order_by(Product.time_posted.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def change_product_status(
    db: AsyncSession,
    product_id: int,
    new_status: ProductStatus
) -> Optional[Product]:
    """
    Изменяет статус продукта.
    """
    product = await get_product_by_id(db, product_id)
    if not product:
        return None

    product.status = new_status.value

    await db.commit()
    await db.refresh(product)
    return product

