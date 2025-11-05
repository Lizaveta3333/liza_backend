from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ProductStatus(str, Enum):
    """Статусы продукта для API схем"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProductBase(BaseModel):
    """
    Базовая схема продукта, содержащая общие поля для всех операций.
    """
    title: str = Field(..., max_length=100, example="Ноутбук Dell XPS 15")
    description: str = Field(..., max_length=1000, example="Мощный ноутбук для работы и игр")
    price: float = Field(..., gt=0, example=89999.99)
    category: str = Field(..., max_length=50, example="Электроника")
    stock: int = Field(..., ge=0, example=10)
    images: Optional[List[str]] = Field(
        None,
        max_items=5,
        example=["https://example.com/image1.jpg"]
    )
    status: Optional[ProductStatus] = Field(default=ProductStatus.ACTIVE)


class ProductCreate(ProductBase):
    """
    Схема для создания нового продукта.
    Наследует все поля из базовой схемы.
    """
    pass


class ProductUpdate(BaseModel):
    """
    Схема для обновления существующего продукта.
    Все поля опциональны - можно обновлять как отдельные поля, так и все сразу.
    """
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=50)
    stock: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = Field(None, max_items=5)
    status: Optional[ProductStatus] = Field(None)


class ProductResponse(ProductBase):
    """
    Схема для возврата данных продукта в API.
    Содержит все поля продукта, включая служебные (id, даты и т.д.)
    """
    id: int = Field(..., description="Уникальный идентификатор продукта", example=1)
    time_posted: datetime = Field(..., description="Дата и время создания продукта", example="2023-01-01T12:00:00")
    seller_id: int = Field(..., description="ID продавца", example=1)

    # Конфигурация Pydantic v2 для работы с ORM
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Ноутбук Dell XPS 15",
                "description": "Мощный ноутбук для работы и игр",
                "price": 89999.99,
                "category": "Электроника",
                "stock": 10,
                "images": ["https://example.com/image1.jpg"],
                "status": "active",
                "time_posted": "2023-01-01T12:00:00",
                "seller_id": 1
            }
        }
    )

