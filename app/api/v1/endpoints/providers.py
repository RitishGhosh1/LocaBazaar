from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.v1.endpoints.dependency import get_current_user
from app.db.session import get_async_db
from app.models.user import User, UserRole
from app.models.services import Service
from app.schemas.user import UserRead, UserCreate
from app.schemas.service import ServiceRead
from app.core.security import get_password_hash

router = APIRouter(prefix="/providers", tags=["providers"])

@router.get("/", response_model=list[UserRead])
async def get_providers(
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(User).where(User.role == UserRole.PROVIDER))
    providers = result.scalars().all()
    return providers

@router.post("/", response_model=UserRead)
async def create_provider(
    provider_in: UserCreate,
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(User).where(User.email == provider_in.email))
    existing_provider = result.scalars().first()
    if existing_provider:
        raise HTTPException(status_code=400, detail="Provider with this email already exists")
    provider_data = provider_in.model_dump()
    plain_password = provider_data.pop("password")
    print(type(plain_password), repr(plain_password))
    hashed_password = get_password_hash(plain_password)
    db_provider = User(**provider_data, hashed_password=hashed_password, role=UserRole.PROVIDER)
    db.add(db_provider)
    await db.commit()
    await db.refresh(db_provider)
    return db_provider

@router.get("/{provider_id}", response_model=list[ServiceRead])
async def get_provider_services(
    provider_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(User).where(User.id == provider_id))
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    service_result = await db.execute(
        select(Service).where(Service.owner_id == provider_id)
    )
    provider_services = service_result.scalars().all()
    return provider_services

@router.delete("/me", status_code=204)
async def delete_provider(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    if user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Not authorized to delete this account")
    if user.is_active:
        user.is_active = False
    else:
        raise HTTPException(status_code=400, detail="Account is already deleted")
    await db.commit()
    return {"detail": "Account deactivated successfully"}