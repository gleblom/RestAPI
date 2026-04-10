from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentCreateDTO(BaseModel):
    title: str
    category_id: int
    unit_id: int
    expires_at: Optional[datetime] = None


class DocumentReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    current_step_index: int
    status_id: int
    category_id: int
    route_id: Optional[int] = None
    author_id: UUID
    created_at: datetime
    updated_at: datetime


class DocumentUpdateDTO(BaseModel):
    id: UUID
    route_id: Optional[int] = None
    status_id: Optional[int] = None
    current_step_index: Optional[int] = None
    title: Optional[str] = None


class DocumentVersionCreateDTO(BaseModel):

    document_id: Optional[UUID] = None
    version_number: Optional[int] = None
    url: str


class DocumentVersionReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: UUID
    version_number: int
    url: str
    created_at: datetime


class DocumentSubmitDTO(BaseModel):
    route_id: int


class NotificationReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    document_id: Optional[UUID]
    message: str
    is_read: bool
    created_at: datetime


class NotificationUpdateDTO(BaseModel):
    is_read: bool


class MVDocumentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    title: str
    status_name: Optional[str] = None
    category_name: Optional[str] = None
    author_email: Optional[str] = None
    route_name: Optional[str] = None
    latest_version_number: Optional[int] = None
    created_at: datetime


class MVNotificationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    email: str
    document_title: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime


class DocumentVersionUploadDTO(BaseModel):

    document_id: UUID
    


class DocumentFileReadDTO(BaseModel):
    document_id: UUID
    version_id: int
    download_name: str
    mime_type: str = "application/pdf"

