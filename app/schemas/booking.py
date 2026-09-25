from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Optional
from app.models.booking import BookingStatus
from datetime import datetime

class BookingCustomerRead(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class BookingServiceRead(BaseModel):
    id: int
    name: str
    price: int
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class BookingBase(BaseModel):
    service_id: int
    
class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    note: Optional[str] = None

class BookingCreate(BookingBase):
    pass 

class BookingRead(BookingBase):
    id: int
    user_id: int
    status: BookingStatus
    booking_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    provider_note: Optional[str] = None
    user: Optional[BookingCustomerRead] = None
    services: Optional[BookingServiceRead] = None

    @computed_field
    @property
    def customer(self) -> Optional[BookingCustomerRead]:
        return self.user

    @computed_field
    @property
    def service(self) -> Optional[BookingServiceRead]:
        return self.services

    model_config = ConfigDict(from_attributes=True)

class BookingListResponse(BaseModel):
    items: list[BookingRead]
    total: int
    next_cursor: Optional[int] = None