from app.models.reviews import Review
from app.models.booking import Booking
from app.schemas.reviews import ReviewCreate, ReviewRead
from app.api.v1.endpoints.dependency import get_current_user
from app.models.user import User

from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

@router.get("/service/{service_id}", response_model=list[ReviewRead])
async def get_reviews_for_service(service_id: int, db: AsyncSession = Depends(get_async_db)):
    result=await db.execute(select(Review).options(selectinload(Review.service)).where(Review.service_id == service_id))
    reviews=result.scalars().all()
    return reviews
