from pydantic import BaseModel, ConfigDict , EmailStr, Field
from typing import Optional
from app.models.user import UserRole
from sqlalchemy import Enum
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    
class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=72,  # Bcrypt's hard limit
        description="Plain text password"
    ) #what apu will receive from the client when creating a provider
 

class UserRead(UserBase): #What api will return to the client
    id: int
    role: UserRole
    is_active: bool
    is_verified:bool
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None