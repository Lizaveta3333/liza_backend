from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db


router = APIRouter()


@router.get("/all")
async def get_orders(db: AsyncSession = Depends(get_db)):
    # return await get_all_users(db)
    return "some orders"
