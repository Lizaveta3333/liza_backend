from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.hashing import hash_password


async def get_user_by_id(db: AsyncSession, id: int) -> Optional[User]:
    stmt = select(User).where(User.id == id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_user_by_email_or_phone(db: AsyncSession, email: str | None = None, phone: str | None = None) -> Optional[User]:
    if email is not None:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()
    elif phone is not None:
        stmt = select(User).where(User.phone == phone)
        result = await db.execute(stmt)
        return result.scalars().first()
    else:
        return None


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    new_user = User(
        phone=user.phone,
        # email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
        avatar=user.avatar,
        about=user.about,
        birth_date=user.birth_date,
        rating=user.rating if user.rating is not None else 5.0,
        is_superuser=False  # Default to False for new users
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_user_data(db: AsyncSession, id: int, new_user: UserUpdate) -> Optional[User]:
    user = await get_user_by_id(db, id)
    if not user:
        return None
    
    update_data = new_user.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "password":
            setattr(user, "hashed_password", hash_password(value))
        else:
            setattr(user, key, value)
    
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except SQLAlchemyError:
        await db.rollback()
        return None


async def delete_user(id: int, db: AsyncSession) -> Optional[User]:
    user = await get_user_by_id(db, id)
    if not user:
        return None
    await db.delete(user)
    await db.commit()  
    return user  


async def get_all_users(db: AsyncSession) -> List[User]:
    stmt = select(User)
    result = await db.execute(stmt)
    return result.scalars().all()
