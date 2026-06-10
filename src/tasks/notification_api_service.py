from uuid import UUID

from src.models.documents import Notification
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.notification_repository import NotificationRepository
from src.tasks.push import process_notification_task


async def create_notification_and_enqueue(
    db: AsyncSession,
    *,
    user_id: UUID,
    document_id: UUID | None,
    title: str,
    body: str,
    event_type: str,
    step_index: int | None = None,
    reason: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        document_id=document_id,
        title=title,
        body=body,
        status="pending",
        data={
            "event_type": event_type,
            "document_id": str(document_id) if document_id else "",
            "step_index": str(step_index) if step_index is not None else "",
            "reason": reason or "",
        },
    )
    await NotificationRepository.create_notification(notification, db)
    await db.commit()
    await db.refresh(notification)

    process_notification_task.delay(notification.id)
    return notification