
from pathlib import Path
from jose import jwt
from jose.exceptions import JWTError
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional
import logging

from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud.user import get_user_by_id
from app.schemas.user import UserResponse

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 дней

BASE_DIR = Path(__file__).resolve().parent.parent
PRIVATE_KEY_PATH = BASE_DIR / ".." / "certs" / "jwt-private.pem"
PUBLIC_KEY_PATH = BASE_DIR / ".." / "certs" / "jwt-public.pem"

def load_key(key_path: Path) -> str:
    try:
        with open(key_path, "r") as key_file:
            return key_file.read()
    except FileNotFoundError:
        logging.error(f"Key file not found: {key_path}")
        raise RuntimeError("JWT key file is missing!")

JWT_PRIVATE_KEY = load_key(PRIVATE_KEY_PATH)
JWT_PUBLIC_KEY = load_key(PUBLIC_KEY_PATH)

def create_jwt(token_type: str, data: Dict[str, Any], expires_delta: int) -> str:
    """Создаёт JWT токен"""
    to_encode = {
        "type": token_type,
        "sub": data.get("sub"),
        "exp": datetime.now(UTC) + timedelta(minutes=expires_delta),
        **data
    }
    return jwt.encode(to_encode, JWT_PRIVATE_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict[str, Any]) -> str:
    return create_jwt("refresh_token", data, REFRESH_TOKEN_EXPIRE_MINUTES)

def create_access_token(data: Dict[str, Any]) -> str:
    return create_jwt("access_token", data, ACCESS_TOKEN_EXPIRE_MINUTES)

def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        logging.warning(f"JWT verification failed: {e}")
        return None

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name="Bearer",
    description="Enter your JWT token (get it from /api/auth/login endpoint)"
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


PUBLIC_ENDPOINTS = [
    "/api/auth/",
    "/api/users/all",
    "/docs",  # Swagger UI
    "/redoc",  # ReDoc
    "/openapi.json",  # JSON-схема API
    "/api/auth/login",  # Login endpoint for Swagger
]

async def refresh_access_token_middleware(request: Request, call_next):
    if any(request.url.path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS):
        return await call_next(request) 

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if access_token:
        payload = verify_jwt(access_token)
        if payload:
            return await call_next(request)  

    if refresh_token:
        refresh_payload = verify_jwt(refresh_token)
        if refresh_payload:
            user_id = refresh_payload.get("sub")
            if not user_id:
                return JSONResponse(status_code=403, content={"detail": "Invalid refresh token"})

            async for db in get_db():
                user = await get_user_by_id(db, int(user_id))
                if not user:
                    return JSONResponse(status_code=403, content={"detail": "User not found"})

                new_access_token = create_access_token({"sub": str(user.id), "email": user.email})
                new_refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

                response = await call_next(request)
                response.set_cookie(key="access_token", value=new_access_token, httponly=True, samesite="Strict")
                response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, samesite="Strict")
                return response

    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})






# from pathlib import Path
# from jose import jwt
# from jose.exceptions import JWTError
# from datetime import datetime, timedelta, UTC
# from typing import Any, Dict, Optional

# ALGORITHM = "RS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
# REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

# BASE_DIR = Path(__file__).resolve().parent.parent
# PRIVATE_KEY_PATH = BASE_DIR / ".." / "certs" / "jwt-private.pem"
# PUBLIC_KEY_PATH = BASE_DIR / ".." / "certs" / "jwt-public.pem"

# def load_key(key_path: Path) -> str:
#     with open(key_path, "r") as key_file:
#         return key_file.read()

# JWT_PRIVATE_KEY = load_key(PRIVATE_KEY_PATH)
# JWT_PUBLIC_KEY = load_key(PUBLIC_KEY_PATH)

# def create_jwt(token_type, data: Dict[str, Any], expires_delta: timedelta) -> str:
#     # to_encode = {"type": token_type}
#     to_encode = {"type": token_type, "sub": data.get("sub", "default_subject")}
#     to_encode.update(data)
#     expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, JWT_PRIVATE_KEY, algorithm=ALGORITHM)

# def create_refresh_token(data: Dict[str, Any]) -> str:
#     return create_jwt(token_type="refresh_token", data=data, expires_delta=REFRESH_TOKEN_EXPIRE_MINUTES)

# def create_access_token(data: Dict[str, Any]) -> str:
#     return create_jwt(token_type="access_token", data=data, expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES)


# def extract_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
#     try:
#         payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[ALGORITHM])
#         return payload
#     except JWTError as e:
#         print(f"JWTError: {e}")
#         return None


# def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
#     try: 
#         return extract_jwt_payload(token)
#     except Exception as e:
#         print(f"Exception: {e}")
#         return None

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
#     payload = verify_jwt(token)
#     if not payload:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

#     user_id = payload.get("sub")
#     if not user_id:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

#     user = await get_user_by_id(db, int(user_id))
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

#     return user

