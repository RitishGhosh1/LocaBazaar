from datetime import datetime,UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_,func
from sqlalchemy.orm import selectinload
from app.db.session import get_async_db
from app.models.services import Service
from app.models.category import Category
from app.models.user import User, UserRole
from app.models.reviews import Review
from app.schemas.user import UserRead
from app.schemas.service import ServiceCreate, ServiceRead, ServiceShortRead,ServiceListResponse
from app.api.v1.endpoints.dependency import get_current_user
from app.core.redis import redis_cache

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

@router.get("/{service_id}",response_model=ServiceRead)
async def get_service_details(service_id:int,db:AsyncSession=Depends(get_async_db)):
    cache_key=f"service_id:{service_id}"
    cached_data=await redis_cache.get(cache_key)
    if cached_data:
        return cached_data
    result=await db.execute(select(Service).options(selectinload(Service.reviews)).where(Service.id==service_id))
    service=result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="SERVICE NOT FOUND")
    service_data = ServiceRead.model_validate(service).model_dump()
    await redis_cache.set(cache_key,service_data,expire=3600)
    return service

@router.get("/", response_model=ServiceListResponse)
async def get_available_services(db:AsyncSession=Depends(get_async_db),
                                 q:Optional[str]=None,
                                 category_id:Optional[int]=None,
                                 category_name:Optional[str]=None,
                                 min_price:Optional[float]=None,
                                 max_price:Optional[float]=None,
                                 skip:int=0,limit:int=10,
                                 cursor:Optional[int]=None):
    cache_key=f"services:q:{q}:cat:{category_id}:s:{skip}:l:{limit}:c:{cursor}:category_name:{category_name}"
    cached_response = await redis_cache.get(cache_key)
    if cached_response:
        return cached_response
    
    query = (
        select(Service)
        .join(User, Service.owner_id == User.id)
        .join(Category, Service.category_id==Category.id)
        .where(Service.is_active == True)
        .where(User.is_active == True) # The second gate
        .options(selectinload(Service.owner))
    )
    if q:
        query = query.where(Service.name.ilike(f"%{q}%"))
    if category_id:
        query = query.where(Service.category_id == category_id)

    if category_name:
        query=query.where(Category.name.ilike(f"&{category_name}"))
    
    if max_price is not None:
        query=query.where(Service.price<max_price)
    if min_price is not None:
        query=query.where(Service.price>min_price)
    # Apply Pagination
    if cursor:
        query = query.where(Service.id > cursor)
    else:
        query = query.offset(skip)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    services = result.scalars().all()

    # 4. METADATA & WRAPPING
    total_count = await db.scalar(select(func.count()).select_from(Service).where(Service.is_active == True))
    next_cursor = services[-1].id if len(services) == limit else None

    # Manually serialize to dicts for Redis
    items_as_dicts = [
        ServiceShortRead.model_validate(s).model_dump() 
        for s in services
    ]
    response_data = {
        "items":items_as_dicts,
        "total": total_count,
        "next_cursor": next_cursor
    }

    # 5. SAVE TO REDIS (Short expire for searches, e.g., 5 mins)
    await redis_cache.set(cache_key, response_data, expire=300)

    return response_data

@router.get("/mine", response_model=list[ServiceRead])
async def get_my_services(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Service).where(Service.owner_id == user.id).options(selectinload(Service.reviews))
    result = await db.execute(stmt)
    return result.scalars().all()

