import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import token_settings
from app.models.user import User
from app.db.session import get_async_db

SECRET_KEY=token_settings.SECRET_KEY
ALGORITHM=token_settings.ALGORITHM

# Clean fallback support: points to your native login route 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception

    email: str = None

    # ---- LAYER 1: TRY DECODING AS NATIVE APP JWT ----
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        # If it's not a valid native JWT, it must be a raw Google Token from the Swagger implicit flow!
        raise credentials_exception
    # ---- LAYER 2: DATABASE SYNCHRONIZATION AND LOOKUP ----
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=403,detail="User account is inactive")

    return user

async def get_current_active_superuser(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user