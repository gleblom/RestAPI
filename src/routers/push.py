from datetime import datetime, timezone
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.models.push_notifications import Device, PushDeliveryState, UserNotificationSettings
from src.repositories.notification_repository import NotificationRepository
from src.services.push_service import delete_notification_service, get_notification_service, mark_notifications_read_service, register_device_service
from src.schemas.push import DeviceListItemDTO, DeviceReadDTO, DeviceRegisterDTO, DeviceStatusDTO, DeviceUpdateDTO, PushSettingsReadDTO, PushSettingsUpdateDTO
from src.security import CurrentUser
from src.database import get_session

router = APIRouter(prefix="/push", tags=["push"])

@router.post("/devices/register")
async def register(
    device: DeviceRegisterDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser
    ):
    await register_device_service(device, db, current_user)
    
def _resolve_device_status(
    *,
    user_push_enabled: bool,
    device: Device,
) -> PushDeliveryState:
    if not user_push_enabled:
        return PushDeliveryState.disabled
    if not device.push_enabled:
        return PushDeliveryState.disabled
    if not device.is_active:
        if device.last_push_status == "invalid_token":
            return PushDeliveryState.invalid_token
        return PushDeliveryState.inactive
    return PushDeliveryState.active
    
@router.delete("/delete/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser
):
    await delete_notification_service(notification_id, db, current_user)
    
@router.post("/mark/read")
async def mark_notifications_read(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser):
    
    await mark_notifications_read_service(db, current_user)
    
@router.get("/{notification_id}")
async def get_notification(
    notification_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser
):
    return await get_notification_service(notification_id, db, current_user)
    
@router.get("/notifications/all")
async def get_all_notifications(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser):
    return await NotificationRepository.get_notifications_by_user(cast(UUID, current_user.user_id), db)

@router.get("/settings", response_model=PushSettingsReadDTO)
async def get_push_settings(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    settings = await db.get(UserNotificationSettings, current_user.user_id)
    if settings is None:
        settings = UserNotificationSettings(user_id=current_user.user_id, push_enabled=True)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.post("/settings", response_model=PushSettingsReadDTO)
async def update_push_settings(
    payload: PushSettingsUpdateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    try:
        settings = await db.get(UserNotificationSettings, current_user.user_id)
        if settings is None:
            settings = UserNotificationSettings(
                user_id=current_user.user_id,
                push_enabled=payload.push_enabled,
            )
            db.add(settings)
        else:
            settings.push_enabled = payload.push_enabled

        await db.commit()
        await db.refresh(settings)
        return settings
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating push settings",
        ) from e


@router.get("/devices", response_model=list[DeviceListItemDTO])
async def list_devices(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    settings = await db.get(UserNotificationSettings, current_user.user_id)
    user_push_enabled = True if settings is None else settings.push_enabled

    result = await db.execute(
        select(Device).where(Device.user_id == current_user.user_id).order_by(Device.last_seen_at.desc().nullslast())
    )
    devices = list(result.scalars().all())

    response: list[DeviceListItemDTO] = []
    for device in devices:
        response.append(
            DeviceListItemDTO(
                id=cast(UUID, device.id),
                device_id=device.device_id,
                platform=device.platform, # type: ignore
                user_push_enabled=user_push_enabled,
                device_push_enabled=device.push_enabled,
                is_active=device.is_active,
                status=_resolve_device_status(
                    user_push_enabled=user_push_enabled,
                    device=device,
                ),
                last_seen_at=cast(datetime, device.last_seen_at),
                last_push_at=device.last_push_at,
                last_push_status=device.last_push_status,
                last_push_error=device.last_push_error,
            )
        )
    return response


@router.get("/devices/{device_id}/status", response_model=DeviceStatusDTO)
async def get_device_status(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    settings = await db.get(UserNotificationSettings, current_user.user_id)
    user_push_enabled = True if settings is None else settings.push_enabled

    result = await db.execute(
        select(Device).where(
            Device.user_id == current_user.user_id,
            Device.device_id == device_id,
        )
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    return DeviceStatusDTO(
        device_id=device.device_id,
        platform=device.platform, # type: ignore
        user_push_enabled=user_push_enabled,
        device_push_enabled=device.push_enabled,
        is_active=device.is_active,
        status=_resolve_device_status(
            user_push_enabled=user_push_enabled,
            device=device,
        ),
        last_seen_at=cast(datetime, device.last_seen_at),
        last_push_at=device.last_push_at,
        last_push_status=device.last_push_status,
        last_push_error=device.last_push_error,
    )

@router.post("/devices/{device_id}", response_model=DeviceReadDTO)
async def update_device_push_state(
    device_id: str,
    payload: DeviceUpdateDTO,
    db:  Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    try:
        result = await db.execute(
            select(Device).where(
                Device.user_id == current_user.user_id,
                Device.device_id == device_id,
            )
        )
        device = result.scalar_one_or_none()
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

        device.push_enabled = payload.push_enabled
        device.disabled_at = None if payload.push_enabled else datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(device)
        return device

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating device",
        ) from e