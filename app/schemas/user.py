from pydantic import BaseModel, ConfigDict , EmailStr, Field
from typing import Optional
from app.models.user import UserRole
from sqlalchemy import Enum
class UserBase(BaseModel):
    name:str
    email:EmailStr
    phone:str
    bio: Optional[str] = None
    
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

    model_config = ConfigDict(from_attributes=True)