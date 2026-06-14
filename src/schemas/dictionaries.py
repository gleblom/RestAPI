from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyReadDTO(BaseModel):# @IgnoreException
    id: UUID
    name: str
    director_id: UUID


class CompanyCreateDTO(BaseModel):# @IgnoreException
    name: str
    director_id: UUID


class CompanyUpdateDTO(BaseModel):# @IgnoreException
    name: str
    company_id: UUID


class RoleCreateDTO(BaseModel):# @IgnoreException
    name: str
    level: int
    unit_id: int | None = None
    category_ids: list[int] = []


class RoleUpdateDTO(BaseModel):# @IgnoreException
    name: Optional[str] = None
    level: Optional[int] = None
    unit_id: Optional[int] = None
    category_ids: Optional[list[int]] = None


class RoleReadDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company_id: UUID | None = None
    level: int
    sort_order: int
    unit_id: int | None = None


class UnitCreateDTO(BaseModel):# @IgnoreException
    name: str
    company_ids: list[UUID] = []


class UnitUpdateDTO(BaseModel):# @IgnoreException
    name: Optional[str] = None
    company_ids: Optional[list[UUID]] = None


class UnitReadDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company_ids: list[UUID] = []


class UnitCompanyLinkDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)
    unit_id: int
    company_id: UUID

    
class RoleCategoryDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)
    role_id: int
    category_ids: list[int] = []

class RoleCategoryReadDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)
    role_id: int
    category_id: int
    
class SimpleDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str


    