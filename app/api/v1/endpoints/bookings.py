from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from sqlalchemy.orm import selectinload
from app.db.session import get_async_db
from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole
from app.models.services import Service
from app.schemas.booking import BookingCreate, BookingRead, BookingStatusUpdate,BookingListResponse
from app.api.v1.endpoints.dependency import get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=BookingRead)
async def create_booking(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service)
        .join(User)
        .where(
            Service.id == booking_in.service_id,
            Service.is_active == True,
            User.is_active == True,
        )
    )
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found or inactive")
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can create bookings")
    if service.owner_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot book your own service")

    booking = Booking(
        **booking_in.model_dump(),
        user_id=user.id,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking

@router.get("/", response_model=BookingListResponse)
async def get_bookings(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
    skip: Optional[int] = 0,
    limit: int = 10,
    cursor: Optional[int] = None
):
    # 1. Base Query based on Role
    if user.role == UserRole.CUSTOMER:
        stmt = select(Booking).where(Booking.user_id == user.id)
    else:
        raise HTTPException(status_code=401,detail="NOT AUTHORISED")
    # else:
    #     # For PROVIDERS: Find bookings where they own the service
    #     stmt = select(Booking).join(Service).where(Service.owner_id == user.id)

    # 2. Get Total Count for this specific user/role
    total_count = await db.scalar(
        select(func.count()).select_from(stmt.subquery())
    )

    # 3. Add Relationships and Order
    stmt = stmt.options(selectinload(Booking.services)).order_by(Booking.id.asc())

    # 4. Apply Pagination Logic
    if cursor:
        stmt = stmt.where(Booking.id > cursor)
    else:
        stmt = stmt.offset(skip)
    
    stmt = stmt.limit(limit)

    # 5. Execute
    result = await db.execute(stmt)
    bookings = result.scalars().all()

    # 6. Metadata
    next_cursor = bookings[-1].id if len(bookings) == limit else None

    return {
        "items": bookings,
        "total": total_count,
        "next_cursor": next_cursor
    }

@router.patch("/{booking_id}", response_model=BookingRead)
async def update_booking_status(
    booking_id: int,
    update_data: BookingStatusUpdate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(Booking)
        .join(Service)
        .where(Booking.id == booking_id, Service.owner_id == user.id)
        .options(selectinload(Booking.services))
    )
    result = await db.execute(stmt)
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=403, detail="you cant change other providers booking status")
    if booking.services.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this booking")
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Only pending or confirmed bookings can be updated")
    booking.status = update_data.status
    if update_data.note:
        booking.provider_note = update_data.note
    booking.update_time = datetime.utcnow()
    await db.commit()
    await db.refresh(booking)
    return booking

