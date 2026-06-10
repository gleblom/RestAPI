
from uuid import UUID

from sqlalchemy import func, select, update

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.push_notifications import Device

class DeviceRepository:
    @staticmethod
    async def upsert_device(
        db: AsyncSession,
        *,
        user_id: UUID,
        device_id: str,
        platform: str,
        push_token: str,
    ) -> Device:
        result = await db.execute(
            select(Device).where(
                Device.user_id == user_id,
                Device.device_id == device_id,
            )
        )
        device = result.scalar_one_or_none()

        if device:
            device.platform = platform
            device.push_token = push_token
            device.is_active = True
            device.last_seen_at = func.now() # type: ignore
            await db.flush()
            return device

        device = Device(
            user_id=user_id,
            device_id=device_id,
            platform=platform,
            push_token=push_token,
            is_active=True,
        )
        db.add(device)
        await db.flush()
        return device

    @staticmethod
    async def get_active_tokens_by_platform(db: AsyncSession, user_id: UUID, platform: str) -> list[str]:
        result = await db.execute(
            select(Device.push_token).where(
                Device.user_id == user_id,
                Device.platform == platform,
                Device.is_active.is_(True),
                Device.push_token.is_not(None),
                Device.push_token != "",
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_device_by_token(
        db: AsyncSession,
        user_id: UUID,
        token: str,
        platform: str | None = None,
    ) -> Device | None:
        stmt = select(Device).where(
            Device.user_id == user_id,
            Device.push_token == token,
        )
        if platform:
            stmt = stmt.where(Device.platform == platform)

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def deactivate_device_by_token(db: AsyncSession, user_id: UUID, token: str) -> None:
        await db.execute(
            update(Device)
            .where(Device.user_id == user_id, Device.push_token == token)
            .values(is_active=False, push_token="")
        )
        await db.flush()
    
    

      