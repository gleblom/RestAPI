from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyReadDTO(BaseModel):# @IgnoreException
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


class RoleUpdateDTO(BaseModel):# @IgnoreException
    name: Optional[str] = None


class RoleReadDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company_id: UUID | None = None


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
    unit_id: int
    company_id: UUID