from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.user import UserBase

class ServiceBase(BaseModel):
    name: str
    category_id: int
    description: Optional[str] = None
    price: int
    image_url: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    price: Optional[int] = None
    image_url: Optional[str] = None

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

from typing import List, Optional

class ServiceListResponse(BaseModel):
    items: List[ServiceShortRead]
    total: int
    next_cursor: Optional[int] = None # The ID to use for the next request

from app.schemas.reviews import ReviewRead
ServiceRead.model_rebuild()
