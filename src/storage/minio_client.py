from __future__ import annotations

from minio import Minio
from src.config import Config

settings = Config()  # type: ignore


minio_client = Minio(
    endpoint = settings.minio_endpoint, 
    access_key = settings.minio_access_key.get_secret_value(), 
    secret_key = settings.minio_secret_key.get_secret_value(),
    secure=settings.minio_secure)
MINIO_BUCKET = settings.minio_bucket