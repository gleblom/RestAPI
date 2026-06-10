

from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreateDTO(BaseModel): # @IgnoreException
    
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr = Field(..., min_length=5, max_length=50)
    password: str = Field(min_length=8)
    phone: Annotated[str , Field(min_length=11, max_length=11)]
    
    
class UserPublicDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    
    
    
class UserTokenDTO(BaseModel): # @IgnoreException
    access_token: str
    token_type: str 
    refresh_token: Optional[str] = None
    
class OtpDTO(BaseModel): # @IgnoreException
    otp_base32: str
    otp_auth_url: str
    
class OtpVerifyDTO(BaseModel): # @IgnoreException
    token: str
    otp_base32: Optional[str]
    
class UserReadDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr = Field(..., min_length=5, max_length=50)
    phone: Optional[str] = Field(min_length=11, max_length=11)
    is_active: bool
    is_email_verified: bool
    created_at: datetime

class UserUpdateDTO(BaseModel): # @IgnoreException
    phone: Annotated[str | None, Field(min_length=11, max_length=11)] = None
    is_active: Optional[bool] = None
    director_id: Optional[UUID] = None
    company_id: Optional[UUID] = None

    
class ProfileDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    first_name: Optional[str] = None
    second_name: Optional[str] = None
    third_name: Optional[str] = None

    role_id: Optional[int] = None
    unit_id: Optional[int] = None
    company_id: Optional[UUID] = None

class UserFullDTO(BaseModel): # @IgnoreException
    
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    
    user_email : Optional[EmailStr] = Field(min_length=1, max_length=32)
    user_phone: Optional[str] = Field(min_length=11, max_length=11)
    
    is_active: Optional[bool]
    is_email_verified: Optional[bool]
    
    otp_enabled: Optional[bool]
    otp_verified: Optional[bool]
    
    
    user_created_at: Optional[datetime]
    user_updated_at: Optional[datetime]
    
    first_name: Optional[str] = Field(min_length=1, max_length=32)
    second_name: Optional[str] = Field(min_length=1, max_length=32)
    third_name: Optional[str] = Field(min_length=1, max_length=32)
    
    company_id: Optional[UUID]
    company_name: Optional[str] = Field(min_length=1, max_length=32)
    
    role_id:Optional[int]
    role_name: Optional[str] = Field(min_length=1, max_length=32)
        
    unit_id:Optional[int]
    unit_name:Optional[str] = Field(min_length=1, max_length=32)
    