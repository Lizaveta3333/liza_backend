from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func

from app.core.database import Base


class OrderStatus(str, Enum):
    """
    Enum статусов заказа.
    Возможные значения:
    - PENDING: Ожидает подтверждения
    - CONFIRMED: Подтвержден
    - COMPLETED: Завершен
    - CANCELLED: Отменен
    """
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(AsyncAttrs, Base):
    """
    Модель заказа в базе данных.
    Содержит информацию о:
    - продукте
    - покупателе
    - количестве
    - общей стоимости
    - статусе заказа
    - дате создания
    - сообщении (опционально)
    """
    __tablename__ = "orders"
    __table_args__ = (
        Index('idx_order_product_buyer', 'product_id', 'buyer_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(Float, nullable=False)
    order_date = Column(DateTime, server_default=func.now(), comment="Дата и время создания заказа")
    status = Column(
        String(20), 
        nullable=False, 
        default=OrderStatus.PENDING.value,
        comment="Текущий статус заказа"
    )
    message = Column(String(500), nullable=True, comment="Сообщение от покупателя")

    # Связь с продуктом (many-to-one)
    product_id = Column(
        Integer, 
        ForeignKey("products.id"), 
        nullable=False, 
        index=True,
        comment="ID продукта"
    )
    product = relationship("Product", back_populates="orders")

    # Связь с покупателем (many-to-one)
    buyer_id = Column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False, 
        index=True,
        comment="ID покупателя"
    )
    buyer = relationship("User", back_populates="orders")

    def __repr__(self):
        return f"Order(id={self.id}, status={self.status}, buyer_id={self.buyer_id}, product_id={self.product_id})"

