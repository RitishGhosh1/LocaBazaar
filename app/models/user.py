from enum import Enum
from sqlalchemy import CheckConstraint, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.services import Service
    from app.models.booking import Booking

class UserRole(str, Enum):
    CUSTOMER = "customer"
    PROVIDER = "provider"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    bio: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(default=UserRole.CUSTOMER)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.utcnow())
    
    # Relationship: A user can own many services (if they are a provider)
    services: Mapped[list["Service"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

    # Relationship: A user can have many bookings (if they are a customer)
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")