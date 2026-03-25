from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.v1.endpoints.dependency import get_current_user
from app.db.session import get_async_db
from app.models.user import User, UserRole
from app.models.services import Service
from app.schemas.user import UserRead, UserCreate
from app.schemas.service import ServiceRead
from app.core.security import get_password_hash

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("/", response_model=UserRead)
async def create_customer(
    customer_in: UserCreate,
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(User).where(User.email == customer_in.email))
    existing_customer = result.scalars().first()
    if existing_customer:
        raise HTTPException(status_code=400, detail="Customer with this email already exists")
    customer_data = customer_in.model_dump()
    plain_password = customer_data.pop("password")
    hashed_password = get_password_hash(plain_password)
    db_customer = User(**customer_data, hashed_password=hashed_password, role=UserRole.CUSTOMER)
    db.add(db_customer)
    await db.commit()
    await db.refresh(db_customer)
    return db_customer

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