
from datetime import datetime, timezone
from typing import cast
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.models.push_notifications import Device
from src.repositories.notification_repository import NotificationRepository
from src.config.main import Config
from src.schemas.push import DeviceRegisterDTO
from src.security import CurrentUser
import logging


settings = Config() # type: ignore

logger = logging.getLogger(__name__)



async def register_device_service(
    payload: DeviceRegisterDTO,
    db: AsyncSession, 
    current_user: CurrentUser,
):
    if payload is None:
        raise HTTPException(status_code=400, detail="Invalid payload")

    try:
        result = await db.execute(
            select(Device).where(
                Device.user_id == current_user.user_id,
                Device.device_id == payload.device_id,
            )
        )
        device = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if device is None:
            device = Device(
                user_id=current_user.user_id,
                device_id=payload.device_id,
                platform=payload.platform,
                push_token=payload.push_token,
                is_active=True,
                push_enabled=True,
                last_seen_at=now,
            )
            db.add(device)
        else:
            device.platform = payload.platform
            device.push_token = payload.push_token
            device.is_active = True
            device.push_enabled = True
            device.last_seen_at = now # type: ignore
            device.disabled_at = None

        await db.commit()
        await db.refresh(device)
        return device

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while registering device",
        ) from e

async def delete_notification_service(notification_id: int, db: AsyncSession, current_user: CurrentUser):
    try:
        notification = await NotificationRepository.get_notification_by_id(notification_id, db)
        
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        if notification.user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Notification is not available")
        await NotificationRepository.delete_notification(db, notification)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from e
    
async def mark_notifications_read_service(db: AsyncSession, current_user: CurrentUser):
    try:
        await NotificationRepository.mark_read(db, cast(UUID, current_user.user_id))
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from e  
     
async def get_notification_service(notification_id: int, db: AsyncSession, current_user: CurrentUser):
    try:
        notification = await NotificationRepository.get_mv_notification_by_id(notification_id, db)
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        return notification
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from e