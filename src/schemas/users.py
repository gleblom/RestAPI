

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreateDTO(BaseModel): # @IgnoreException
    
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    password: str = Field(min_length=8)
    phone: Optional[str] = None
    
    
class UserPublicDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    
    
    
class UserTokenDTO(BaseModel): # @IgnoreException
    access_token: str
    token_type: str 
    refresh_token: str
    
    
class UserReadDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    phone: Optional[str]
    is_active: bool
    is_email_verified: bool
    created_at: datetime

class UserUpdateDTO(BaseModel): # @IgnoreException
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    director_id: Optional[UUID] = None
    company_id: Optional[UUID] = None

    
class ProfileDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    first_name: Optional[str]
    second_name: Optional[str]
    third_name: Optional[str]

    role_id: Optional[int]
    unit_id: Optional[int]
    company_id: Optional[UUID]