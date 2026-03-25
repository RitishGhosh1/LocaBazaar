from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.models.booking import BookingStatus
from datetime import datetime

class BookingBase(BaseModel):
    service_id: int
    
class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    note: Optional[str] = None

class BookingCreate(BookingBase):
    pass 

class BookingRead(BookingBase):
    id:int
    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)