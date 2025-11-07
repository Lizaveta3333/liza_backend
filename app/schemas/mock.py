from pydantic import BaseModel
from typing import List, Optional



class UserModelSchema(BaseModel):
    id: int
    phone: str
    email: str
    password: str
    full_name: str
    avatar: str | None = None
    about: str | None = None
    birth_date: str | None = None
    rating: int = 5
    orders: List[OrderModelSchema]
    notifications: List[NotificationModelSchema]
    chats: List[ChatModelSchema]
    comments: List[CommentModelSchema]

class CommentModelSchema(BaseModel):
    id: int
    user_id: int
    text: str
    rating: int

class OrderModelSchema(BaseModel):
    id: int
    type_of_order: 'customer' | 'employee' = 'customer'
    customer_id: int
    employee_id: int
    description: str
    conditions: str
    images: List[str]
    priority: str = "low"
    order_date: str
    delivery_date: str
    status: str = "open"
    payment_method: str = "cash"
    price: int
    address: str = "Минск"
    users_offers: List[int] = []

class NotificationModelSchema(BaseModel):
    id: int
    user_id: int
    from_whom: str | None = None
    title: str
    text: str
    date: str
    is_read: bool = False

class ChatModelSchema(BaseModel):
    id: int
    users_id: List[int]
    messages: List[MessageModelSchema]

class MessageModelSchema(BaseModel):
    id: int
    user_id: int
    text: str
    date: str
    is_read: bool = False
