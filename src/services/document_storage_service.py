from __future__ import annotations

import uuid

from fastapi import HTTPException, UploadFile, status
from minio.error import S3Error
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.document_repository import DocumentRepository
from src.services.document_file_service import ensure_pdf_file
from src.storage.minio_client import MINIO_BUCKET, minio_client


async def upload_document_version_to_storage(
    db: AsyncSession,
    document_id,
    upload: UploadFile,
):
    pdf_path, original_name, original_mime = await ensure_pdf_file(upload)

    document = await DocumentRepository.get_document_by_id(document_id, db)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    latest_version = await DocumentRepository.get_latest_document_version(document_id, db)
    next_version_number = 1 if latest_version is None else latest_version.version_number + 1

    object_name = f"documents/{document_id}/v{next_version_number}/{uuid.uuid4()}.pdf"

    try:
        file_size = pdf_path.stat().st_size
        with pdf_path.open("rb") as fh:
            minio_client.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=object_name,
                data=fh,
                length=file_size,
                content_type="application/pdf",
            )
    except S3Error as e:
        raise HTTPException(status_code=500, detail="Error while saving file to MinIO") from e
    finally:
        try:
            pdf_path.unlink(missing_ok=True)
        except Exception:
            pass

    return {
        "version_number": next_version_number,
        "storage_object_name": object_name,
        "original_file_name": original_name,
        "mime_type": "application/pdf",
        "file_size": file_size,
    }


def get_minio_object_stream(object_name: str):
    try:
        return minio_client.get_object(MINIO_BUCKET, object_name)
    except S3Error as e:
        raise HTTPException(status_code=404, detail="File not found in storage") from e


def get_presigned_download_url(object_name: str) -> str:
    try:
        return minio_client.presigned_get_object(MINIO_BUCKET, object_name)
    except S3Error as e:
        raise HTTPException(status_code=500, detail="Cannot create download URL") from e

