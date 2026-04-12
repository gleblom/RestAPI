from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentApprovalCreateDTO(BaseModel):# @IgnoreException
    version_id: int
    step_index: int


class DocumentApprovalActionDTO(BaseModel):# @IgnoreException
    is_approved: bool
    comment: Optional[str] = None

class RouteCreateDTO(BaseModel):# @IgnoreException
    name: str


class RouteNodeDTO(BaseModel):# @IgnoreException
    approver_id: UUID
    step_index: int


class RouteReadDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: UUID

class DocumentApprovalReadDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_id: int
    approver_id: UUID
    step_index: int
    is_approved: Optional[bool]
    comment: Optional[str]
    created_at: datetime
    
class MVApprovalDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: UUID
    title: str
    version_number: int

    approver_email: Optional[str]
    step_index: int
    is_approved: Optional[bool]