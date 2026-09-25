from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.v1.endpoints.dependency import get_current_user
from app.db.session import get_async_db
from app.models.user import User, UserRole
from app.models.services import Service
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.schemas.service import ServiceRead
from app.core.security import get_password_hash
from app.services.email import queue_verification_email
import logging

logger=logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: UserCreate,
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(
        select(User).where(User.email == customer_in.email)
    )

    existing_customer = result.scalars().first()

    if existing_customer:
        if existing_customer.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Account with this email already exists!!",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Account with this email already exists but is not verified"
            )
    customer_data = customer_in.model_dump()

    plain_password = customer_data.pop("password")
    hashed_password = get_password_hash(plain_password)

    db_customer = User(
        **customer_data,
        hashed_password=hashed_password,
        role=UserRole.CUSTOMER,
    )

    db.add(db_customer)
    await db.commit()
    await db.refresh(db_customer)
    try:
        await queue_verification_email(
                user_id=db_customer.id,
                email=db_customer.email,
            )
    except Exception as e:
       logger.warning(f"User {db_customer.id} created, but verification email failed to queue: {e}")

    return db_customer

@router.get("/me", response_model=UserRead)
async def get_customer_profile(
    user: User = Depends(get_current_user),
):
    if user.role != UserRole.CUSTOMER and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized as a customer")
    return user

@router.patch("/me", response_model=UserRead)
async def update_customer_profile(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    if user.role != UserRole.CUSTOMER and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized as a customer")

    update_data = user_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] is not None:
        trimmed_name = update_data["name"].strip()
        if not trimmed_name:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        user.name = trimmed_name
    if "phone" in update_data:
        user.phone = update_data["phone"].strip() if update_data["phone"] else None
    if "bio" in update_data:
        user.bio = update_data["bio"].strip() if update_data["bio"] else None
    if "avatar_url" in update_data:
        user.avatar_url = update_data["avatar_url"].strip() if update_data["avatar_url"] else None

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/me", status_code=204)
async def delete_customer(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Not authorized to delete this account")
    if user.is_active:
        user.is_active = False
    else:
        raise HTTPException(status_code=400, detail="Account is already deleted")
    await db.commit()
    return {"detail": "Account deactivated successfully"}