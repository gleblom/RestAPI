from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.models.documents import Notification
from src.models.push_notifications import  Device


class NotificationSyncRepository:
    @staticmethod
    def get_by_id(db: Session, notification_id: int) -> Notification | None:
        return db.execute(
            select(Notification).where(Notification.id == notification_id)
        ).scalar_one_or_none()

    @staticmethod
    def mark_sent(db: Session, notification_id: int) -> None:
        db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status="sent", sent_at=func.now(), error=None)
        )

    @staticmethod
    def mark_failed(db: Session, notification_id: int, error: str) -> None:
        db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status="failed", error=error)
        )


class DeviceSyncRepository:
    @staticmethod
    def get_active_tokens(db: Session, user_id, platform: str) -> list[str]:
        result = db.execute(
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
    def deactivate_token(db: Session, user_id, token: str) -> None:
        db.execute(
            update(Device)
            .where(Device.user_id == user_id, Device.push_token == token)
            .values(is_active=False, push_token="")
        )