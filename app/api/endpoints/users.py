from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.crud.user import get_all_users, get_user_by_id, update_user_data, delete_user
from app.core.security import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/all", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    return await get_all_users(db)


@router.get("/get/{id}", response_model=UserResponse)
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/get", response_model=UserResponse)
async def get_users(user: UserResponse = Depends(get_current_user)):
    return user


@router.patch("/me/update", response_model=UserResponse)
async def update_user(
    user: UserUpdate = Depends(), 
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    if not user.dict(exclude_unset=True):
        raise HTTPException(status_code=400, detail="No fields to update")

    id = current_user.id
    updated_user = await update_user_data(db, id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user


@router.delete("/me/delete")
async def delete_user_data(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    is_deleted = await delete_user(current_user.id, db)
    if not is_deleted:
        raise HTTPException(status_code=404, detail="User not found")

    response.set_cookie(key="access_token", value="", max_age=0, httponly=True, samesite="Strict")
    response.set_cookie(key="refresh_token", value="", max_age=0, httponly=True, samesite="Strict")

    return {"success": 200, "message": "User deleted successfully"}
