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
async def login_google(request: Request):
    # Standard static redirect URI extraction linked directly to your auth_google route name
    redirect_uri = request.url_for('auth_google')
    print("Using redirect URI:", redirect_uri) 
    
    # Fire the standard authorization handshake step directly with Google's servers
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google")
async def auth_google(request: Request, db: AsyncSession = Depends(get_async_db)):
    try:
        # 1. Capture the authorization code token package back from Google
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
    
    # 2. Query the PostgreSQL database to check if this user already exists
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    
    # 3. Dynamic User Ingestion Loop
    if not user:
        # Create and write a brand new user record to your clean tables
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            role=UserRole.CUSTOMER,  # Default system registration constraint
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.google_id:
        # Link their Google identifier if they signed up natively via email/password first
        user.google_id = google_id
        await db.commit()
        await db.refresh(user)

    # 4. Generate your internal application's high-privilege access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # 🎯 THE PURE JSON TEXT HAND-OFF FIX:
    # This strips away redirect strings and outputs raw token data directly to the view!
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