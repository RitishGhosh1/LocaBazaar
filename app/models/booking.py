from app.models.base import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship,mapped_column, Mapped
from datetime import datetime, timezone
from enum import Enum
from app.models.user import User
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.services import Service

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REJECTED = "rejected"

class Booking(Base):
    __tablename__="bookings"

    id:Mapped[int] = mapped_column(primary_key=True, index=True)
    service_id:Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    user_id:Mapped[int]=mapped_column(Integer, ForeignKey("users.id"),nullable=False)
    status:Mapped[BookingStatus]=mapped_column(String,default=BookingStatus.PENDING)
    booking_time:Mapped[datetime]=mapped_column(default=lambda: datetime.utcnow())
    update_time:Mapped[datetime]=mapped_column(default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    provider_note:Mapped[str]=mapped_column(String, nullable=True)
    # Relationships
    services = relationship("Service", back_populates="bookings")
    user = relationship("User", back_populates="bookings")