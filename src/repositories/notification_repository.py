from uuid import UUID

from src.models.documents import Notification

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.views import MVNotification

class NotificationRepository:
    
    @staticmethod
    async def create_notification(notification: Notification, db: AsyncSession):
        db.add(notification)
        
        await db.flush()
        
        return notification
    
    @staticmethod
    async def get_notifications_by_id(notification: int, db: AsyncSession):
        result = await db.execute(select(Notification).where(Notification.id == notification))
        
        return result.scalar_one_or_none();
    
    @staticmethod
    async def get_notifications_by_user(user_id: UUID, db: AsyncSession):
        result = await db.execute(select(MVNotification).where(MVNotification.user_id == user_id))
        
        return result.all()
    
    @staticmethod
    async def delete_notifcation(notification: Notification, db: AsyncSession):
       await db.delete(notification)
        
       await db.flush()
    