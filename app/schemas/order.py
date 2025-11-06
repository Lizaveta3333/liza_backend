from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class OrderStatus(str, Enum):
    """
    Схема статусов заказа для API.
    """
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderBase(BaseModel):
    """
    Базовая схема заказа, содержащая общие поля для всех операций.
    """
    quantity: int = Field(..., gt=0, description="Количество товара", example=2)
    message: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Сообщение от покупателя",
        example="Пожалуйста, доставьте до 18:00"
    )
    status: Optional[OrderStatus] = Field(
        default=OrderStatus.PENDING,
        description="Текущий статус заказа",
        example="pending"
    )


class OrderCreate(BaseModel):
    """
    Схема для создания нового заказа.
    """
    product_id: int = Field(..., description="ID продукта", example=1)
    quantity: int = Field(..., gt=0, description="Количество товара", example=2)
    message: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Сообщение от покупателя",
        example="Пожалуйста, доставьте до 18:00"
    )


class OrderUpdate(BaseModel):
    """
    Схема для обновления существующего заказа.
    Все поля опциональны - можно обновлять как отдельные поля, так и все сразу.
    """
    quantity: Optional[int] = Field(None, gt=0, description="Обновленное количество")
    message: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Обновленное сообщение"
    )
    status: Optional[OrderStatus] = Field(
        None,
        description="Новый статус заказа"
    )


class OrderResponse(OrderBase):
    """
    Схема для возврата данных заказа в API.
    Содержит все поля заказа, включая служебные (id, даты и т.д.)
    """
    id: int = Field(..., description="Уникальный идентификатор заказа", example=1)
    order_date: datetime = Field(..., description="Дата и время создания заказа", example="2023-01-01T12:00:00")
    product_id: int = Field(..., description="ID продукта", example=1)
    buyer_id: int = Field(..., description="ID покупателя", example=1)
    total_price: float = Field(..., description="Общая стоимость заказа", example=179999.98)

    # Конфигурация Pydantic v2 для работы с ORM
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "product_id": 1,
                "buyer_id": 1,
                "quantity": 2,
                "total_price": 179999.98,
                "status": "pending",
                "message": "Пожалуйста, доставьте до 18:00",
                "order_date": "2023-01-01T12:00:00"
            }
        }
    )

