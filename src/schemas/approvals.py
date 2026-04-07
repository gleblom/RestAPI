from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentApprovalCreateDTO(BaseModel):
    version_id: int
    step_index: int


class DocumentApprovalActionDTO(BaseModel):
    is_approved: bool
    comment: Optional[str] = None

class RouteCreateDTO(BaseModel):
    name: str


class RouteNodeDTO(BaseModel):
    approver_id: UUID
    step_index: int


class RouteReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: UUID

class DocumentApprovalReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_id: int
    approver_id: UUID
    step_index: int
    is_approved: Optional[bool]
    comment: Optional[str]
    created_at: datetime
    
class MVApprovalDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: UUID
    title: str
    version_number: int

    approver_email: Optional[str]
    step_index: int
    is_approved: Optional[bool]