import logging

from firebase_admin import messaging

from src.firebase.firebase import get_firebase_app

logger = logging.getLogger(__name__)


class FcmClient:
    def send_multicast(self, *, tokens, title, body, data):
        if not tokens:
            return None

        app = get_firebase_app()

        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data,
        )

        return messaging.send_each_for_multicast(message, app=app)