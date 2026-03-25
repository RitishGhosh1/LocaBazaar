from sqlalchemy import String, ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.services import Service
    from app.models.user import User
    
class Review(Base): 
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # 3NF Foreign Keys
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # Relationships
    service: Mapped["Service"] = relationship("Service", back_populates="reviews",lazy="selectin")
    user: Mapped["User"] = relationship("User",lazy="selectin")

    # Ensure rating is between 1 and 5 at the DB level
    __table_args__ = (CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),)