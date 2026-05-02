from __future__ import annotations
from app.models.reviews import Review
from app.models.booking import Booking
from app.schemas.reviews import ReviewCreate, ReviewRead, ReviewListResponse
from app.api.v1.endpoints.dependency import get_current_user
from app.models.user import User
from app.core.redis import redis_cache

from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from sqlalchemy.orm import selectinload

router= APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/",response_model=ReviewCreate)
async def create_review(review: ReviewCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    
    if current_user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can create reviews")
    booking=await db.execute(select(Booking).options(selectinload(Booking.services)).where(Booking.service_id == review.service_id, Booking.user_id == current_user.id, Booking.status == "completed"))
    if not booking.scalars().first():
        raise HTTPException(status_code=400, detail="You can only review services you have completed bookings for")
    review_exists=await db.execute(select(Review).options(selectinload(Review.service)).where(Review.service_id == review.service_id, Review.user_id == current_user.id))
    if review_exists.scalars().first():
        raise HTTPException(status_code=400, detail="You have already reviewed this service")
    new_review=Review(**review.model_dump(), user_id=current_user.id)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review

@router.get("/{review_id}", response_model=ReviewRead)
async def get_review(review_id: int, db: AsyncSession = Depends(get_async_db)):
    result=await db.execute(select(Review).where(Review.id == review_id))
    review=result.scalars().first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@router.get("/service/{service_id}", response_model=ReviewListResponse)
async def get_reviews_for_service(
    service_id: int, 
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 10,
    cursor: int|None = None
):
    # 1. Unique Cache Key per Service and Page
    cache_key = f"reviews:svc:{service_id}:s:{skip}:l:{limit}:c:{cursor}"
    
    cached_data = await redis_cache.get(cache_key)
    if cached_data:
        return cached_data

    # 2. Base Query
    stmt = select(Review).where(Review.service_id == service_id).order_by(Review.id.asc())

    # 3. Total Count for this service
    total_count = await db.scalar(
        select(func.count()).select_from(Review).where(Review.service_id == service_id)
    )

    # 4. Apply Pagination
    if cursor:
        stmt = stmt.where(Review.id > cursor)
    else:
        stmt = stmt.offset(skip)
    
    stmt = stmt.limit(limit)
    
    result = await db.execute(stmt)
    reviews = result.scalars().all()

    # 5. Metadata & Serialization
    next_cursor = reviews[-1].id if len(reviews) == limit else None
    
    # model_dump() ensures we have a clean dict for Redis
    items_as_dicts = [ReviewRead.model_validate(r).model_dump() for r in reviews]

    response_data = {
        "items": items_as_dicts,
        "total": total_count,
        "next_cursor": next_cursor
    }

    # 6. Cache for 10 minutes
    await redis_cache.set(cache_key, response_data, expire=600)

    return response_data