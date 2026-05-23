import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import SECRET_KEY, ALGORITHM
from app.models.user import User
from app.db.session import get_async_db

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
    google_id: str = None
    name: str = None
    is_google_token = False

    # ---- LAYER 1: TRY DECODING AS NATIVE APP JWT ----
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        # If it's not a valid native JWT, it must be a raw Google Token from the Swagger implicit flow!
        is_google_token = True

    # ---- LAYER 2: INTERCEPT RAW GOOGLE TOKENS FROM SWAGGER UI ----
    if is_google_token:
        async with httpx.AsyncClient() as client:
            # Send the token to Google's standard OIDC userinfo endpoint to verify it
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise credentials_exception
            
            user_info = response.json()
            email = user_info.get("email")
            google_id = user_info.get("sub")
            name = user_info.get("name", email.split("@")[0])

    # ---- LAYER 3: DATABASE SYNCHRONIZATION AND LOOKUP ----
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    # THE CRUCIAL DIRECTIVE: If logging in via Swagger for the first time, write them to DB!
    if not user:
        if is_google_token:
            user = User(
                email=email,
                name=name,
                google_id=google_id,
                # Importing your specific Enum structure here is recommended
                role="customer",  
                is_active=True,
                is_superuser=False  # System security safety baseline
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            raise credentials_exception
    elif is_google_token and not user.google_id:
        # Link their Google Account if they previously registered natively via password
        user.google_id = google_id
        await db.commit()
        await db.refresh(user)

    return user

async def get_current_active_superuser(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user