from fastapi import APIRouter, Depends, HTTPException, Request,Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_async_db
from app.models.user import User, UserRole
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from app.core.oauth import oauth
from app.core.config import config
from app.core.verification import verify_verification_token, generate_verification_token
from app.api.v1.endpoints.dependency import get_current_user
from app.schemas.user import UserRead, UserUpdate
from app.services.email import queue_verification_email
FRONTEND_URL=config.FRONTEND_URL
from app.core.rabbitmq import rabbitmq_manager
router = APIRouter(prefix="/auth", tags=["auth"])

# @router.post("/test-rabbit")
# async def test_rabbit():
#     await rabbitmq_manager.publish({
#         "job_type": "test",
#         "message": "Hello RabbitMQ"
#     })
#     return {"message": "Message published"}

@router.get("/verify-email")
async def verify_email(token:str, db:AsyncSession=Depends(get_async_db)):
    email=verify_verification_token(token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )
    result = await db.execute(
        select(User).where(User.email==email)
    )
    user=result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if user.is_verified:
        return {"message":"Email already verified"}

    user.is_verified=True
    await db.commit()
    await db.refresh(user)
    return {"message":"Email verified successfully"}

@router.post("/verify-email")
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
):
    if current_user.is_verified:
        return {"message": "Email already verified"}

    await queue_verification_email(
        user_id=current_user.id,
        email=current_user.email,
    )
    return {"message": "Verification email sent successfully"}

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is not active")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    role_str = user.role.value if hasattr(user.role, "value") else user.role
    access_token = create_access_token(
        data={
            "sub": user.email,
            "id": user.id,
            "name": user.name,
            "role": role_str,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
        },
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "bio": user.bio,
            "role": role_str,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
        },
    }

@router.get("/me", response_model=UserRead)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.patch("/me", response_model=UserRead)
async def update_my_profile(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    update_data = user_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] is not None:
        trimmed_name = update_data["name"].strip()
        if not trimmed_name:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        current_user.name = trimmed_name
    if "phone" in update_data:
        current_user.phone = update_data["phone"].strip() if update_data["phone"] else None
    if "bio" in update_data:
        current_user.bio = update_data["bio"].strip() if update_data["bio"] else None

    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.get("/login/google")
async def login_google(request: Request):
    # Standard static redirect URI extraction linked directly to your auth_google route name
    redirect_uri = request.url_for('auth_google')
    print("Using redirect URI:", redirect_uri) 
    
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
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if not user:
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            role=UserRole.CUSTOMER,
            is_active=True,
            is_superuser=False,
            is_verified=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.is_active:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=account_inactive",
            status_code=302
        )
    elif not user.google_id:
        user.google_id = google_id
        user.is_verified = True
        await db.commit()
        await db.refresh(user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
        "sub": user.email,
        "id": user.id,
        "name": user.name,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        }, expires_delta=access_token_expires
    )
    return RedirectResponse(
        url=(
            f"{FRONTEND_URL}/auth/callback"
            f"#access_token={access_token}"
            f"&token_type=bearer"
        ),
        status_code=302
    )