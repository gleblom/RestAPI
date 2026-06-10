from src.celery_app import celery_app
from src.tasks.sync_db import SyncSessionLocal
from src.tasks.notification_worker_service import NotificationWorkerService
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, lazy=False, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def process_notification_task(self, notification_id: int) -> None:  # @IgnoreException
    logger.info("Celery task process_notification_task started for id=%s", notification_id)
    try:
        with SyncSessionLocal() as db:
            service = NotificationWorkerService(db)
            service.send_notification(notification_id)
    except Exception as exc:
        logger.exception("Celery task process_notification_task failed for id=%s: %s", notification_id, exc)
        raise
        