from sqlalchemy import Column, Integer, String, Float, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from app.core.database import Base

class User(AsyncAttrs, Base):
    __tablename__ = "users"

    # id = Column(Integer, primary_key=True, index=True)
    # username = Column(String, unique=True, index=True, nullable=False)
    # email = Column(String, unique=True, index=True, nullable=False)
    # hashed_password = Column(String, nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False) # reqr
    # email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False) # reqr
    full_name = Column(String, nullable=False) # reqr
    about = Column(String, nullable=True) # optional
    avatar = Column(String, nullable=True) # optional
    birth_date = Column(Date, nullable=True) # optional
    rating = Column(Float, default=5)  # reqr
    is_superuser = Column(Boolean, default=False, nullable=False)  # reqr
    # profile_images
    
    # Relationships
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    
