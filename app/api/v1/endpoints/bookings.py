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
            User.is_verified == True,
        )
    )
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found or inactive")
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can create bookings")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Customer email must be verified to create bookings")
    if service.owner_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot book your own service")

    booking = Booking(
        **booking_in.model_dump(),
        user_id=user.id,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    await db.commit()
    
    # Reload with relationships for full response
    stmt = (
        select(Booking)
        .where(Booking.id == booking.id)
        .options(selectinload(Booking.services), selectinload(Booking.user))
    )
    result = await db.execute(stmt)
    return result.scalars().first()

@router.get("/", response_model=BookingListResponse)
async def get_bookings(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
    skip: Optional[int] = 0,
    limit: int = 10,
    cursor: Optional[int] = None
):
    # 1. Base Query based on Role
    if user.is_superuser:
        stmt = select(Booking)
    elif user.role == UserRole.PROVIDER:
        stmt = select(Booking).join(Service).where(Service.owner_id == user.id)
    elif user.role == UserRole.CUSTOMER:
        stmt = select(Booking).where(Booking.user_id == user.id)
    else:
        raise HTTPException(status_code=401, detail="NOT AUTHORISED")

    # 2. Get Total Count for this specific user/role
    total_count = await db.scalar(
        select(func.count()).select_from(stmt.subquery())
    )

    # 3. Add Relationships and Order (latest first)
    stmt = stmt.options(
        selectinload(Booking.services),
        selectinload(Booking.user)
    ).order_by(Booking.id.desc())

    # 4. Apply Pagination Logic
    if cursor:
        stmt = stmt.where(Booking.id < cursor)
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
        .where(Booking.id == booking_id)
        .options(
            selectinload(Booking.services),
            selectinload(Booking.user)
        )
    )
    result = await db.execute(stmt)
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_provider = booking.services.owner_id == user.id
    is_customer = booking.user_id == user.id
    is_admin = user.is_superuser

    if not (is_provider or is_customer or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to update this booking")

    # Customer permissions: can only cancel pending or confirmed bookings
    if is_customer and not (is_provider or is_admin):
        if update_data.status != BookingStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Customers can only cancel bookings")
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED, BookingStatus.REJECTED]:
            raise HTTPException(status_code=400, detail="Cannot cancel a booking that is already resolved")
    else:
        # Provider / Admin permissions
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            raise HTTPException(status_code=400, detail="Only pending or confirmed bookings can be updated")

    booking.status = update_data.status
    if update_data.note:
        booking.provider_note = update_data.note
    booking.update_time = datetime.utcnow()
    await db.commit()
    
    # Reload with relationships
    stmt = (
        select(Booking)
        .where(Booking.id == booking.id)
        .options(
            selectinload(Booking.services),
            selectinload(Booking.user)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()

@router.post("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            selectinload(Booking.services),
            selectinload(Booking.user)
        )
    )
    result = await db.execute(stmt)
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != user.id and booking.services.owner_id != user.id and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")

    if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED, BookingStatus.REJECTED]:
        raise HTTPException(status_code=400, detail="Cannot cancel a booking that is already resolved")

    booking.status = BookingStatus.CANCELLED
    booking.update_time = datetime.utcnow()
    await db.commit()
    
    # Reload with relationships
    stmt = (
        select(Booking)
        .where(Booking.id == booking.id)
        .options(
            selectinload(Booking.services),
            selectinload(Booking.user)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()

