from uuid import UUID


from src.models.documents import Notification

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.views import MVNotification

class NotificationRepository:
    
    @staticmethod
    async def create_notification(notification: Notification, db: AsyncSession):
        db.add(notification)
        
        await db.flush()
        
        return notification
    
    @staticmethod
    async def get_notification_by_id(notification: int, db: AsyncSession):
        result = await db.execute(select(Notification).where(Notification.id == notification))
        
        return result.scalar_one_or_none();
    @staticmethod
    async def get_mv_notification_by_id(notification: int, db: AsyncSession):
        result = await db.execute(select(MVNotification).where(MVNotification.id == notification))
        
        return result.scalar_one_or_none();
    
    @staticmethod
    async def get_notifications_by_user(user_id: UUID, db: AsyncSession):
        result = await db.execute(select(MVNotification).where(MVNotification.user_id == user_id))
        
        return result.scalars().all()
    
    @staticmethod
    async def delete_pending_approval_notifications(
        db: AsyncSession,
        *,
        user_id: UUID,
        document_id: UUID,
        step_index: int,
    ) -> None:
       
        stmt = (
            delete(Notification)
            .where(Notification.user_id == user_id) 
            .where(Notification.document_id == document_id)
            .where(Notification.status.in_(["pending", "sent"]))
            .where(Notification.data["event_type"].astext == "approval_required")
            .where(Notification.data["step_index"].astext == str(step_index))
        )
        await db.execute(stmt)
        await db.flush()
    
    
    @staticmethod
    async def mark_sent(db: AsyncSession, notification_id: int) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status="sent", sent_at=func.now(), error=None)
        )
        await db.flush()

    @staticmethod
    async def mark_failed(db: AsyncSession, notification_id: int, error: str) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status="failed", error=error)
        )
        await db.flush()
        
    @staticmethod
    async def delete_notification(db: AsyncSession, notification: Notification) -> None:
        await db.delete(notification)
        
        await db.flush()
        
    @staticmethod
    async def mark_read(db: AsyncSession, user_id: UUID):
        await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id)
            .values(is_read=True)
        )
        
        await db.flush()
    