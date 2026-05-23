from fastapi import APIRouter, Depends, HTTPException, Request,Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_async_db
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserCreate
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta, timezone, datetime
from app.core.oauth import oauth
import urllib.parse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/login/google")
async def login_google(
    request: Request, 
    # # 1. Accept a dynamic parameter indicating where the tokens should land
    # frontend_redirect: str = Query(default="https://locabazaar-api.onrender.com/docs")
):
    redirect_uri = request.url_for('auth_google')
    print("Using redirect URI:", redirect_uri) 
    
    # 2. Google's state parameter takes any string and hands it back untouched.
    # We pass the frontend's target destination inside it!
    # extra_params = {"state": frontend_redirect}
    
    return await oauth.google.authorize_redirect(request, redirect_uri, **extra_params)


@router.get("/google")
async def auth_google(request: Request, db: AsyncSession = Depends(get_async_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        print("OAuth Error:", str(e))   
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
        
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")
    
    email = user_info.get('email')
    google_id = user_info.get('sub')
    name = user_info.get('name')
    
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    
    if not user:
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            role=UserRole.CUSTOMER,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.google_id:
        user.google_id = google_id
        await db.commit()
        await db.refresh(user)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # # 3. EXTRACT THE STATE DESTINATION BACK FROM GOOGLE
    # # Google passes back all original query params under request.query_params
    # frontend_destination = request.query_params.get("state")
    
    # # Fallback to the safe Swagger documentation if no state query existed
    # if not frontend_destination:
    #     frontend_destination = "https://locabazaar-api.onrender.com/docs"
        
    # # 4. THE HAND-OFF FIX: Divert traffic dynamically
    # # Build your destination parameter URL safely
    # redirect_url = f"{frontend_destination}?token={access_token}&token_type=bearer"
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_superuser": user.is_superuser
        }
    }


