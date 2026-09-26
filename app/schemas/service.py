from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.schemas.user import UserBase

class ServiceBase(BaseModel):
    name: str
    category_id: int
    description: Optional[str] = None
    price: int
    image_url: Optional[str] = None

class UploadRead(BaseModel):
    id: int
    url: str
    filename: str
    model_config = ConfigDict(from_attributes=True)

class ServiceCreate(ServiceBase):
    image_ids: list[int] = Field(default_factory=list, max_length=10)

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
    images: list[UploadRead] = Field(default_factory=list)
    model_config=ConfigDict(from_attributes=True)

class ServiceRead(ServiceBase):
    id:int
    owner_id:int
    is_active: bool
    reviews:list["ReviewRead"] = Field(default_factory=list)
    images: list[UploadRead] = Field(default_factory=list)
    model_config=ConfigDict(from_attributes=True)

from typing import List, Optional

class ServiceListResponse(BaseModel):
    items: List[ServiceShortRead]
    total: int
    next_cursor: Optional[int] = None # The ID to use for the next request

from app.schemas.reviews import ReviewRead
ServiceRead.model_rebuild()
