from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.asyncio import AsyncAttrs
from app.core.database import Base

class User(AsyncAttrs, Base):
    __tablename__ = "users"

    # id = Column(Integer, primary_key=True, index=True)
    # username = Column(String, unique=True, index=True, nullable=False)
    # email = Column(String, unique=True, index=True, nullable=False)
    # hashed_password = Column(String, nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    about = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    rating = Column(Float, default=5)
