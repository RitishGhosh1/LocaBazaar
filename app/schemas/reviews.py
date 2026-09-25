from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    comment: Optional[str] = Field(None, max_length=500)
    service_id: int
    model_config = ConfigDict(from_attributes=True)

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating must be between 1 and 5")
    comment: Optional[str] = Field(None, max_length=500)
    model_config = ConfigDict(from_attributes=True)

class ReviewRead(ReviewBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class ReviewListResponse(BaseModel):
    items: list[ReviewRead]
    total: int
    next_cursor: Optional[int] = None