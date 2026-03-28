from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    comment: Optional[str] = Field(None, max_length=500)
    service_id: int

class ReviewCreate(ReviewBase):
    pass

class ReviewRead(ReviewBase):
    id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)

class ReviewListResponse(BaseModel):
    items: list[ReviewRead]
    total: int
    next_cursor: Optional[int] = None