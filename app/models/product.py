from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs

from app.core.database import Base


class ProductStatus(str, Enum):
    """Статусы продукта"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class Product(AsyncAttrs, Base):
    """
    Модель продукта в базе данных PostgreSQL.
    """
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint('price > 0', name='check_price_positive'),
        CheckConstraint('stock >= 0', name='check_stock_non_negative'),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    price = Column(Float, nullable=False)
    images = Column(JSON, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    stock = Column(Integer, nullable=False, default=0)
    time_posted = Column(DateTime, server_default=func.now())
    status = Column(String(20), nullable=False, default=ProductStatus.ACTIVE.value)

    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    seller = relationship("User", back_populates="products")
    orders = relationship("Order", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title}', seller_id={self.seller_id})>"

