from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from sqlalchemy import String, Integer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.services import Service

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    services = relationship("Service", back_populates="category")

