
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.auth import ResponseTokensSchema
from app.crud.user import get_user_by_email_or_phone, create_user, get_user_by_id
from app.utils.hashing import verify_password
from app.core.security import create_access_token, create_refresh_token, verify_jwt
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    existing_user = await get_user_by_email_or_phone(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")

    new_user = await create_user(db, user)
    return new_user


@router.post("/login", response_model=ResponseTokensSchema)
async def login_user(
    response: Response, 
    db: AsyncSession = Depends(get_db),
    user: UserLogin = Depends()
    # user: OAuth2PasswordRequestForm = Depends()
    ):
    """Аутентификация пользователя"""
    existing_user = await get_user_by_email_or_phone(db, user.username)
    if not existing_user or not verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(existing_user.id), "phone": existing_user.phone})
    refresh_token = create_refresh_token({"sub": str(existing_user.id), "phone": existing_user.phone})

    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="Strict")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="Strict")

    return ResponseTokensSchema(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(response: Response):
    """Выход из системы (удаление токенов)"""
    response.set_cookie(key="access_token", value="", max_age=0, httponly=True, samesite="Strict")
    response.set_cookie(key="refresh_token", value="", max_age=0, httponly=True, samesite="Strict")
    return {"message": "Logged out successfully"}


# @router.post("/refresh", response_model=ResponseTokensSchema)
# async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
#     """Обновление access-токена по refresh-токену"""
#     token = request.cookies.get("refresh_token")
#     payload = verify_jwt(token)
    
#     if not payload:
#         logger.warning("Invalid refresh token received: %s", token)
#         raise HTTPException(status_code=403, detail="Invalid or expired refresh token")

#     sub = payload.get("sub")
#     if sub is None:
#         raise HTTPException(status_code=403, detail="Invalid refresh token")

#     user = await get_user_by_id(db, int(sub))
#     if user is None:
#         raise HTTPException(status_code=403, detail="User not found")

#     access_token = create_access_token({"sub": str(user.id), "email": user.email})
#     refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

#     response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="Strict")
#     response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="Strict")

#     return ResponseTokensSchema(access_token=access_token, refresh_token=refresh_token)

