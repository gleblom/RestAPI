from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentCreateDTO(BaseModel):# @IgnoreException
    title: str
    category_id: int
    unit_id: int
    expires_at: Optional[datetime] = None


class DocumentReadDTO(BaseModel):# @IgnoreException
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


class DocumentUpdateDTO(BaseModel):# @IgnoreException
    id: UUID
    route_id: Optional[int] = None
    status_id: Optional[int] = None
    current_step_index: Optional[int] = None
    title: Optional[str] = None


class DocumentVersionCreateDTO(BaseModel):# @IgnoreException

    document_id: Optional[UUID] = None
    version_number: Optional[int] = None
    storage_object_name: str
    original_file_name: str
    mime_type: str
    file_size: int


class DocumentVersionReadDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: UUID
    version_number: int
    url: str
    created_at: datetime


class DocumentSubmitDTO(BaseModel):# @IgnoreException
    route_id: int


class NotificationReadDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    document_id: Optional[UUID]
    message: str
    is_read: bool
    created_at: datetime


class NotificationUpdateDTO(BaseModel):# @IgnoreException
    is_read: bool


class MVDocumentDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    title: str
    status_name: Optional[str] = None
    category_name: Optional[str] = None
    author_email: Optional[str] = None
    route_name: Optional[str] = None
    latest_version_number: Optional[int] = None
    created_at: datetime


class MVNotificationDTO(BaseModel):# @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    email: str
    document_title: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime


class DocumentVersionUploadDTO(BaseModel):# @IgnoreException

    document_id: UUID
    


class DocumentFileReadDTO(BaseModel):# @IgnoreException
    document_id: UUID
    version_id: int
    download_name: str
    mime_type: str = "application/pdf"

