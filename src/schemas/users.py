

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreateDTO(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    password: str = Field(min_length=8)
    phone: Optional[str] = None
    
    
class UserPublicDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    
    
    
class UserTokenDTO(BaseModel):
    access_token: str
    token_type: str 
    refresh_token: str
    
    
class UserReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    phone: Optional[str]
    is_active: bool
    is_email_verified: bool
    created_at: datetime

class UserUpdateDTO(BaseModel):
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    director_id: Optional[UUID] = None
    company_id: Optional[UUID] = None

    
class ProfileDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str]
    second_name: Optional[str]
    third_name: Optional[str]

    role_id: Optional[int]
    unit_id: Optional[int]
    company_id: Optional[UUID]