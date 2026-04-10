from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyReadDTO(BaseModel):
    company_name: str
    director_id: UUID


class CompanyCreateDTO(BaseModel):
    company_name: str
    director_id: UUID


class CompanyUpdateDTO(BaseModel):
    company_name: str
    company_id: UUID


class RoleCreateDTO(BaseModel):
    name: str


class RoleUpdateDTO(BaseModel):
    name: Optional[str] = None


class RoleReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company_id: UUID | None = None


class UnitCreateDTO(BaseModel):
    name: str
    company_ids: list[UUID] = []


class UnitUpdateDTO(BaseModel):
    name: Optional[str] = None
    company_ids: Optional[list[UUID]] = None


class UnitReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company_ids: list[UUID] = []


class UnitCompanyLinkDTO(BaseModel):
    unit_id: int
    company_id: UUID