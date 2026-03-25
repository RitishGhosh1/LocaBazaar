from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime, CheckConstraint
from datetime import datetime, timezone
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.booking import Booking
    from app.models.category import Category
    from app.models.reviews import Review

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    price: Mapped[int] = mapped_column(nullable=False) # Mandated for V1
    category_id:Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    is_active: Mapped[bool] = mapped_column(default=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    #relationships
    owner: Mapped["User"] = relationship(back_populates="services")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="services")
    category:Mapped["Category"] = relationship(back_populates="services")
    reviews: Mapped[list["Review"]] = relationship(back_populates="service")