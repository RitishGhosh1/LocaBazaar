from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.user import UserBase

class ServiceBase(BaseModel):
    name: str
    category_id: int
    description: Optional[str] = None
    price: int

class ServiceCreate(ServiceBase):
    pass

class ServiceShortRead(ServiceBase):
    id:int
    owner_id:int
    is_active: bool
    model_config=ConfigDict(from_attributes=True)

class ServiceRead(ServiceBase):
    id:int
    owner_id:int
    is_active: bool
    reviews:list["ReviewRead"] = []
    model_config=ConfigDict(from_attributes=True)

from app.schemas.reviews import ReviewRead
ServiceRead.model_rebuild()
