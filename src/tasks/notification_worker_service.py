from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.documents import Notification
from src.tasks.fcm import FcmClient
from src.tasks.wns import WnsClient
from src.tasks.sync_push_repository import (
    DeviceSyncRepository,
    NotificationSyncRepository,
)
import logging

logger = logging.getLogger(__name__)


class NotificationWorkerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.fcm = FcmClient()
        self.wns = WnsClient()

    def send_notification(self, notification_id: int) -> None:
        logger.info("Processing notification id=%s", notification_id)
        notification = NotificationSyncRepository.get_by_id(self.db, notification_id)
        if notification is None:
            logger.warning("Notification id=%s not found", notification_id)
            return

        if notification.status == "sent":
            return

        data = {
            "notification_id": str(notification.id),
            "document_id": str(notification.document_id or ""),
            "event_type": str((notification.data or {}).get("event_type", "")),
            "step_index": str((notification.data or {}).get("step_index", "")),
            "reason": str((notification.data or {}).get("reason", "")),
        }

        try:
            self._send_android(notification, data)
            self._send_windows(notification)

            NotificationSyncRepository.mark_sent(self.db, notification.id)
            self.db.commit()
        except Exception as exc:
            logger.exception("Failed to send notification id=%s: %s", notification_id, exc)
            self.db.rollback()
            try:
                NotificationSyncRepository.mark_failed(self.db, notification.id, str(exc))
                self.db.commit()
            except Exception:
                self.db.rollback()
            raise

    def _send_android(self, notification: Notification, data: dict[str, str]) -> None:
        tokens = DeviceSyncRepository.get_active_tokens(self.db, notification.user_id, "android")
        if not tokens:
            return
        logger.info("Sending Android FCM notification id=%s to %d tokens", notification.id, len(tokens))

        response = self.fcm.send_multicast(
            tokens=tokens,
            title=notification.title,
            body=notification.body,
            data=data,
        )
        if response is None:
            return
        for idx, resp in enumerate(response.responses):
            if resp.success:
                continue

            token = tokens[idx]
            code = getattr(resp.exception, "code", None) or str(resp.exception)
            logger.warning("FCM send failed for token=%s code=%s", token, code)

            if "UNREGISTERED" in code or "registration-token-not-registered" in code:
                logger.info("Deactivating token for user=%s token=%s", notification.user_id, token)
                DeviceSyncRepository.deactivate_token(self.db, notification.user_id, token)

    def _send_windows(self, notification: Notification) -> None:
        tokens = DeviceSyncRepository.get_active_tokens(self.db, notification.user_id, "windows")
        if not tokens:
            return
        logger.info("Sending Windows notifications id=%s to %d channels", notification.id, len(tokens))

        for channel_uri in tokens:
            try:
                self.wns.send_toast(
                    channel_uri=channel_uri,
                    title=notification.title,
                    body=notification.body,
                    document_id=str(notification.document_id or ""),
                    notification_id=notification.id,
                )
            except Exception as exc:  # propagate to outer try/except to mark failed
                logger.exception("WNS send failed for channel=%s notification=%s: %s", channel_uri, notification.id, exc)
                raise