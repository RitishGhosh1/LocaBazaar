from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update, delete
from app.db.session import get_async_db
from app.models.user import User, UserRole
from app.models.services import Service
from app.models.booking import Booking, BookingStatus
from app.models.reviews import Review
from app.schemas.user import UserRead
from app.schemas.service import ServiceListResponse, ServiceShortRead
from app.schemas.booking import BookingListResponse, BookingRead, BookingStatusUpdate
from app.schemas.reviews import ReviewListResponse, ReviewRead
from app.api.v1.endpoints.dependency import get_current_user
from app.core.redis import redis_cache

# --- Governance Dependency ---
async def get_superuser(user: User = Depends(get_current_user)):
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Superuser access required"
        )
    return user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    total_people=await db.execute(select(func.count()).select_from(User))
    total_users = await db.execute(select(func.count()).select_from(User).where(User.role == UserRole.CUSTOMER))
    total_providers = await db.execute(select(func.count()).select_from(User).where(User.role == UserRole.PROVIDER,User.is_superuser.is_(False)))
    total_services = await db.execute(select(func.count()).select_from(Service))
    pending_bookings = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.PENDING)
    )
    completed_bookings = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.COMPLETED)
    )
    total_reviews = await db.execute(select(func.count()).select_from(Review))
    
    return {
        "total_people":total_people.scalar() or 0,
        "total_users": total_users.scalar() or 0,
        "total_providers": (total_providers.scalar() or 0),
        "total_services": total_services.scalar() or 0,
        "pending_bookings": pending_bookings.scalar() or 0,
        "completed_bookings": completed_bookings.scalar() or 0,
        "total_reviews": total_reviews.scalar() or 0,
    }


@router.get("/users", response_model=list[UserRead])
async def admin_list_users(
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser)
):
    result = await db.execute(select(User).order_by(User.id.asc()))
    return result.scalars().all()


@router.get("/providers", response_model=list[UserRead])
async def admin_list_providers(
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser)
):
    result = await db.execute(
    select(User)
    .where(
        User.role == UserRole.PROVIDER,
        User.is_superuser.is_(False)
    )
    .order_by(User.id.asc())
)
    return result.scalars().all()


@router.get("/services", response_model=ServiceListResponse)
async def admin_list_services(
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
    skip: int = 0,
    limit: int = 50,
):
    count_stmt = select(func.count()).select_from(Service)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = select(Service).order_by(Service.id.desc()).offset(skip).limit(limit)
    services = (await db.execute(stmt)).scalars().all()
    items = [ServiceShortRead.model_validate(s) for s in services]
    return ServiceListResponse(items=items, total=total, next_cursor=None)


@router.get("/bookings", response_model=BookingListResponse)
async def admin_list_bookings(
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
    skip: int = 0,
    limit: int = 50,
):
    count_stmt = select(func.count()).select_from(Booking)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(Booking).order_by(Booking.id.desc()).offset(skip).limit(limit)
    bookings = (await db.execute(stmt)).scalars().all()
    items = [BookingRead.model_validate(b) for b in bookings]
    return BookingListResponse(items=items, total=total, next_cursor=None)


@router.get("/reviews", response_model=ReviewListResponse)
async def admin_list_reviews(
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
    skip: int = 0,
    limit: int = 50,
):
    count_stmt = select(func.count()).select_from(Review)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(Review).order_by(Review.id.desc()).offset(skip).limit(limit)
    reviews = (await db.execute(stmt)).scalars().all()
    items = [ReviewRead.model_validate(r) for r in reviews]
    return ReviewListResponse(items=items, total=total, next_cursor=None)


@router.patch("/users/{user_id}/deactivate")
async def admin_deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own admin account.")
    if target_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot deactivate another superuser")
    
    await db.execute(
        update(Service).where(Service.owner_id == target_user.id).values(is_active=False)
    )

    await db.execute(
        update(Booking).where((Booking.user_id == target_user.id) | (Booking.service_id.in_(select(Service.id).where(Service.owner_id == target_user.id))),
                              Booking.status.in_([BookingStatus.PENDING,BookingStatus.CONFIRMED]))
                              .values(status=BookingStatus.CANCELLED)
        )
    target_user.is_active = False
    await db.commit()

    await redis_cache.clear_pattern("service_id:*")
    await redis_cache.clear_pattern("services:q:*")

    return {"detail": f"User {user_id} has been suspended."}

@router.patch("/users/{user_id}/reactivate")
async def admin_reactivate_user(
    user_id:int,
    db:AsyncSession = Depends(get_async_db),
    admin: User=Depends(get_superuser)
):
    result=await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404,detail="User not found")
    if target_user.is_active:
        raise HTTPException(status_code=400,detail="User is already active")
    target_user.is_active=True
    await db.commit()
    await db.refresh(target_user)

    return {
        "message":"User account reactivated successfully",
        "user id":target_user.id,
        "is_active":target_user.is_active
    }

@router.delete("/users/{user_id}")
async def admin_hard_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.is_active:
        raise HTTPException(status_code=400, detail="Only deactivated accounts can be permanently deleted.")

    if target_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superusers cannot be deleted via API.")

    user_services_subquery = select(Service.id).where(Service.owner_id == target_user.id)

    await db.execute(
        delete(Review).where(
            or_(Review.user_id == target_user.id, Review.service_id.in_(user_services_subquery))
        )
    )
    await db.execute(
        delete(Booking).where(
            or_(Booking.user_id == target_user.id, Booking.service_id.in_(user_services_subquery))
        )
    )
    await db.execute(delete(Service).where(Service.owner_id == target_user.id))
    await db.delete(target_user)
    await db.commit()

    await redis_cache.clear_pattern("service_id:*")
    await redis_cache.clear_pattern("services:q:*")

    return {"detail": "Record permanently removed from database."}


@router.patch("/services/{service_id}/suspend")
async def admin_suspend_service(
    service_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service.is_active = False
    await db.commit()

    await redis_cache.clear(f"service_id:{service_id}")
    await redis_cache.clear_pattern("services:q:*")

    return {"detail": "Service suspended for review."}


@router.patch("/services/{service_id}/unsuspend")
async def admin_unsuspend_service(
    service_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service.is_active = True
    await db.commit()

    await redis_cache.clear(f"service_id:{service_id}")
    await redis_cache.clear_pattern("services:q:*")

    return {"detail": "Service unsuspended successfully."}


@router.patch("/bookings/{booking_id}/status", response_model=BookingRead)
async def admin_update_booking_status(
    booking_id: int,
    status_in: BookingStatusUpdate,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = status_in.status
    await db.commit()
    await db.refresh(booking)

    return booking


@router.delete("/reviews/{review_id}")
async def admin_delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalars().first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    service_id = review.service_id
    await db.delete(review)
    await db.commit()

    await redis_cache.clear_pattern(f"reviews:svc:{service_id}:*")

    return {"detail": "Review deleted successfully."}
