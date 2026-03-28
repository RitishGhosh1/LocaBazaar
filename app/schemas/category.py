from pydantic import BaseModel, ConfigDict
from typing import Optional,List,TYPE_CHECKING



class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True) #allows Pydantic to read the data from SQLAlchemy models using attribute access

class CategoryReadWithServices(CategoryRead):
    services: List["ServiceRead"] = [] 
    model_config = ConfigDict(from_attributes=True)
from app.schemas.service import ServiceRead
CategoryReadWithServices.model_rebuild()



