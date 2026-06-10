import json
import logging
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials

from src.config.main import Config

logger = logging.getLogger(__name__)
settings = Config()  # type: ignore


@lru_cache
def get_firebase_app():

    if not settings.firebase_service_account_json:
        raise RuntimeError("Firebase credentials not configured")

    try:
        data = json.loads(settings.firebase_service_account_json)
    except Exception as e:
        logger.exception("Invalid Firebase JSON")
        raise

    try:
        # Попробовать получить уже созданное приложение
        return firebase_admin.get_app()
    except ValueError:
        # Не существует → создаём
        logger.info("Initializing Firebase app")

        cred = credentials.Certificate(data)
        firebase_admin.initialize_app(cred, name="fastapi")
        
        app = firebase_admin.get_app("fastapi")
        

        logger.info("Firebase initialized")
        return app