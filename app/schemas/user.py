
from pydantic import BaseModel, EmailStr
from typing import Optional

from pydantic import BaseModel, EmailStr
from datetime import date

class UserCreate(BaseModel):
    phone: str
    # email: EmailStr
    password: str
    full_name: str
    avatar: str | None = None
    about: str | None = None
    birth_date: date | None = None
    rating: float = 5.00


# class UserUpdate(BaseModel):
#     phone: Optional[str] = None
#     email: Optional[EmailStr] = None
#     password: Optional[str] = None
#     full_name: Optional[str] = None
#     avatar: Optional[str] = None
#     about: Optional[str] = None
#     birth_date: Optional[date] = None
#     rating: Optional[int] = None
class UserUpdate(BaseModel):
    phone: str | None = None
    # email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None
    avatar: str | None = None
    about: str | None = None
    birth_date: date | None = None  
    rating: float | None = None

class UserLogin(BaseModel):
    username: str # make a phone validation
    password: str

class UserResponse(BaseModel):
    id: int
    phone: str
    # email: str
    full_name: str
    avatar: str | None = None
    about: str | None = None
    birth_date: date | None = None
    rating: float = 5.00

    class Config:
        from_attributes = True


class User(BaseModel):
    id: int
    phone: str
    # email: str
    full_name: str
    avatar: str | None = None
    about: str | None = None
    birth_date: date | None = None
    rating: float = 5.00
    