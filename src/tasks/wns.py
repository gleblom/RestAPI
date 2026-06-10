from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests
import logging

from src.config.main import Config

settings = Config()  # type: ignore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WnsAccessToken:
    value: str
    expires_at: datetime


class WnsClient:
    def __init__(self) -> None:
        self._cached_token: WnsAccessToken | None = None

    def _get_access_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._cached_token and self._cached_token.expires_at > now + timedelta(minutes=2):
            return self._cached_token.value

        resp = requests.post(
            f"https://login.microsoftonline.com/{settings.client_directory}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.client_id,
                "client_secret": settings.client_secret.get_secret_value(),
                "scope": "https://wns.windows.com/.default",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._cached_token = WnsAccessToken(
            value=access_token,
            expires_at=now + timedelta(seconds=expires_in),
        )
        return access_token

    @staticmethod
    def _build_toast_xml(title: str, body: str, document_id: str, notification_id: str) -> str:
        # launch — это строка, которую клиент сможет распарсить при клике
        launch = html.escape(f"document_id={document_id}&notification_id={notification_id}", quote=True)

        def esc(text: str) -> str:
            return html.escape(text, quote=False)
        
        print(launch)

        return f"""<?xml version="1.0" encoding="utf-8"?>
<toast launch="{launch}">
  <visual>
    <binding template="ToastGeneric">
      <text>{esc(title)}</text>
      <text>{esc(body)}</text>
    </binding>
  </visual>
</toast>"""

    def send_toast(self, *, channel_uri: str, title: str, body: str, document_id: str, notification_id: int) -> None:
        try:
            access_token = self._get_access_token()
            xml = self._build_toast_xml(title, body, document_id, str(notification_id))

            logger.info("Sending WNS toast: channel=%s notification_id=%s document_id=%s", channel_uri, notification_id, document_id)

            resp = requests.post(
                channel_uri,
                data=xml.encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-WNS-Type": "wns/raw",
                    "Content-Type": "application/octet-stream",
                },
                timeout=15,
            )
        except requests.RequestException as exc:  # pragma: no cover - network/error handling
            logger.exception("Failed to send WNS toast for notification=%s: %s", notification_id, exc)

            raise