

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.push_notifications import DevicePlatform, PushDeliveryState


    
@dataclass(slots=True)
class PushNotificationPayload:
    user_id: UUID
    document_id: UUID
    title: str
    body: str
    event_type: str
    step_index: int | None = None
    reason: str | None = None

class PushSettingsReadDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    push_enabled: bool
    updated_at: datetime


class PushSettingsUpdateDTO(BaseModel): # @IgnoreException
    push_enabled: bool = Field(..., description="Включить или выключить push для пользователя")


class DeviceRegisterDTO(BaseModel): # @IgnoreException
    device_id: str = Field(min_length=1, max_length=255)
    platform: DevicePlatform
    push_token: str = Field(min_length=1)


class DeviceUpdateDTO(BaseModel): # @IgnoreException
    push_enabled: bool


class DeviceReadDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    device_id: str
    platform: DevicePlatform
    push_token: str
    is_active: bool
    push_enabled: bool
    last_seen_at: datetime | None
    last_push_at: datetime | None
    last_push_status: str | None
    last_push_error: str | None
    disabled_at: datetime | None


class DeviceStatusDTO(BaseModel): # @IgnoreException
    device_id: str
    platform: DevicePlatform
    user_push_enabled: bool
    device_push_enabled: bool
    is_active: bool
    status: PushDeliveryState
    last_seen_at: datetime | None
    last_push_at: datetime | None
    last_push_status: str | None
    last_push_error: str | None
    


class DeviceListItemDTO(DeviceStatusDTO): # @IgnoreException
    id: UUID



class DeviceRegisterResponseDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    device_id: str
    platform: DevicePlatform
    is_active: bool
    push_enabled: bool