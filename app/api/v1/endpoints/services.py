from datetime import datetime,UTC
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_,func
from sqlalchemy.orm import selectinload
from app.db.session import get_async_db
from app.models.services import Service
from app.models.category import Category
from app.models.user import User, UserRole
from app.models.reviews import Review
from app.models.uploads import Upload
from app.schemas.user import UserRead
from app.schemas.service import ServiceCreate, ServiceRead, ServiceShortRead, ServiceListResponse, ServiceUpdate
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
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="User is not verified")
    if user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="User is not a provider")
    image_ids = list(dict.fromkeys(service_in.image_ids))
    if image_ids:
        image_result = await db.execute(
            select(Upload).where(
                Upload.id.in_(image_ids),
                Upload.owner_id == user.id,
                Upload.purpose == "service",
                Upload.service_id.is_(None),
            ).with_for_update()
        )
        uploads_by_id = {upload.id: upload for upload in image_result.scalars().all()}
        if len(uploads_by_id) != len(image_ids):
            raise HTTPException(
                status_code=400,
                detail="One or more uploaded service images are invalid or already in use.",
            )
        service_images = [uploads_by_id[image_id] for image_id in image_ids]
    else:
        service_images = []

    service_data = service_in.model_dump(exclude={"image_ids"})
    if service_images:
        service_data["image_url"] = service_images[0].url
    db_service = Service(**service_data, owner_id=user.id, images=service_images)
    db.add(db_service)
    await db.commit()
    await redis_cache.clear_pattern("services:q:*")
    return db_service

@router.get("/mine", response_model=list[ServiceRead])
async def get_my_services(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Service).where(Service.owner_id == user.id).options(
        selectinload(Service.reviews), selectinload(Service.images)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{service_id}/toggle", response_model=ServiceRead)
async def toggle_service_status(
    service_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    
    result = await db.execute(
        select(Service).options(selectinload(Service.reviews), selectinload(Service.images)).where(Service.id == service_id)
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
    await redis_cache.clear(f"service_id:{service_id}")
    await redis_cache.clear_pattern("services:q:*")
    return service

@router.patch("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: int,
    service_update: ServiceUpdate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service).options(selectinload(Service.reviews), selectinload(Service.images)).where(Service.id == service_id)
    )
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    if service.owner_id != user.id and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to edit this service")

    update_data = service_update.model_dump(exclude_unset=True)
    if "category_id" in update_data and update_data["category_id"] is not None:
        cat_check = await db.execute(select(Category).where(Category.id == update_data["category_id"]))
        if not cat_check.scalars().first():
            raise HTTPException(status_code=400, detail="Invalid category ID")

    for key, value in update_data.items():
        setattr(service, key, value)

    service.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(service)
    await redis_cache.clear(f"service_id:{service_id}")
    await redis_cache.clear_pattern("services:q:*")
    return service

@router.delete("/{service_id}", status_code=204)
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service).options(selectinload(Service.images)).where(Service.id == service_id)
    )
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    if service.owner_id != user.id and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this service")

    image_filenames = [image.filename for image in service.images]
    await db.delete(service)
    await db.commit()
    for filename in image_filenames:
        try:
            os.remove(os.path.join(os.getcwd(), "uploads", filename))
        except FileNotFoundError:
            pass
    await redis_cache.clear(f"service_id:{service_id}")
    await redis_cache.clear_pattern("services:q:*")
    return None

@router.get("/{service_id}", response_model=ServiceRead)
async def get_service_details(service_id:int,db:AsyncSession=Depends(get_async_db)):
    cache_key=f"service_id:{service_id}"
    cached_data=await redis_cache.get(cache_key)
    if cached_data:
        return cached_data
    result=await db.execute(
        select(Service)
        .options(selectinload(Service.reviews), selectinload(Service.images))
        .where(Service.id == service_id)
    )
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
                                 skip:int=Query(0,ge=0),limit:int=Query(10,ge=1,le=1000),
                                 cursor:Optional[int]=Query(None,ge=0)):
    cache_key=f"services:q:{q}:cat:{category_id}:min_p:{min_price}:max_p:{max_price}:s:{skip}:l:{limit}:c:{cursor}:category_name:{category_name}"
    cached_response = await redis_cache.get(cache_key)
    if cached_response:
        return cached_response
    
    query = (
        select(Service)
        .join(User, Service.owner_id == User.id)
        .join(Category, Service.category_id==Category.id)
        .where(Service.is_active == True)
        .where(User.is_active == True) # The second gate
        .where(User.is_verified == True) # The third gate
        .options(selectinload(Service.owner), selectinload(Service.images))
    )

    if q:
        query = query.where(Service.name.ilike(f"%{q}%"))
    if category_id:
        query = query.where(Service.category_id == category_id)
    if category_name:
        query=query.where(Category.name.ilike(f"%{category_name}%"))
    if max_price is not None:
        query=query.where(Service.price<=max_price)
    if min_price is not None:
        query=query.where(Service.price>=min_price)

    subquery=query.subquery()
    count_query=select(func.count()).select_from(subquery)
    total_count=await db.scalar(count_query)

    if cursor:
        query = query.where(Service.id > cursor)
    if not cursor:
        query = query.offset(skip)
    query = query.order_by(Service.id).limit(limit)

    result = await db.execute(query)
    services = result.scalars().all()
    next_cursor = services[-1].id if len(services) == limit else None

    items_as_dicts = [
        ServiceShortRead.model_validate(s).model_dump() 
        for s in services
    ]
    response_data = {
        "items":items_as_dicts,
        "total": total_count,
        "next_cursor": next_cursor
    }
    await redis_cache.set(cache_key, response_data, expire=300)
    return response_data


