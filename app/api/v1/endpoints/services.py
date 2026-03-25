from datetime import datetime,UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from app.db.session import get_async_db
from app.models.services import Service
from app.models.category import Category
from app.models.user import User, UserRole
from app.schemas.user import UserRead
from app.schemas.service import ServiceCreate, ServiceRead, ServiceShortRead
from app.api.v1.endpoints.dependency import get_current_user

router = APIRouter(prefix="/services", tags=["services"])

@router.post("/", response_model=ServiceShortRead, status_code=201)
async def create_service(
    service_in: ServiceCreate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    if user.is_active == False:
        raise HTTPException(status_code=403, detail="User is not active")
    if user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="User is not a provider")
    db_service = Service(**service_in.model_dump(), owner_id=user.id)
    db.add(db_service)
    await db.commit()
    await db.refresh(db_service)
    return db_service

@router.patch("/{service_id}/toggle", response_model=ServiceRead)
async def toggle_service_status(
    service_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service).where(Service.id == service_id)
    )
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    if service.owner_id != user.id:
        raise HTTPException(status_code=401, detail="Not authorized to modify this service")
    service.is_active = not service.is_active
    service.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(service)
    return service

@router.get("/", response_model=list[ServiceShortRead])
async def get_available_services(db:AsyncSession=Depends(get_async_db)):
    query = (
        select(Service)
        .join(User, Service.owner_id == User.id)
        .where(Service.is_active == True)
        .where(User.is_active == True) # The second gate
        .options(selectinload(Service.owner),selectinload(Service.reviews))
    )
    result = await db.execute(query)
    services = result.scalars().all()
    return services

@router.get("/mine", response_model=list[ServiceRead])
async def get_my_services(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Service).where(Service.owner_id == user.id).options(selectinload(Service.reviews))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/",response_model=ServiceShortRead)
async def search_services(db:AsyncSession=Depends(get_async_db),
                          q:Optional[str]=None,
                          category_name:Optional[str]=None,
                          min_price:Optional[float]=None,
                          max_price:Optional[float]=None):
    query=(select(Service).join(Category, Service.category_id==Category.id)
           .options(selectinload(Service.owner),selectinload(Service.reviews),selectinload(Service.category)))
    filters=[]
    #Category
    if category_name:
        filters.append(Category.name.ilike(f"%{category_name}%"))
    #Text Search
    if q:
        filters.append(or_(Service.name.ilike(f"%{q}%"),Service.description.ilike(f"%{q}%")))
    if min_price:
        filters.append(Service.price >= min_price)
    if max_price:
        filters.append(Service.price <= max_price)
    if filters:
        query.where(and_(*filters))
    result=await db.execute(query)
    return result.scalars().all()

    