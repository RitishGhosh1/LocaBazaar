from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_async_db
from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole
from app.models.services import Service
from app.schemas.booking import BookingCreate, BookingRead, BookingStatusUpdate
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

@router.get("/", response_model=list[BookingRead])
async def get_bookings(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):

    if user.role == UserRole.CUSTOMER:
        stmt = select(Booking).where(Booking.user_id == user.id).options(
            selectinload(Booking.services)
        )
    else:
        stmt = (
            select(Booking)
            .join(Service)
            .where(Service.owner_id == user.id)
            .options(selectinload(Booking.services))
        )
    result = await db.execute(stmt)
    return result.scalars().all()

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