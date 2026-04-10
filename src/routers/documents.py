from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repositories.document_repository import DocumentRepository
from schemas.documents import (
    DocumentCreateDTO,
    DocumentReadDTO,
    DocumentSubmitDTO,
    DocumentVersionCreateDTO,
    DocumentVersionReadDTO,
)
from security import CurrentUser
from services.approval_service import approve_document_service, reject_document_service, submit_document_service
from services.document_service import (
    create_document_service,
    create_document_version_service,
    get_document_service,
    upload_document_version_service,
)
from services.document_storage_service import get_minio_object_stream, get_presigned_download_url

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", status_code=status.HTTP_200_OK, response_model=DocumentReadDTO)
async def get_document(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    try:
        return await get_document_service(db, current_user, document_id)
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")



@router.post("", response_model=DocumentReadDTO, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await create_document_service(db, current_user, document)


@router.post("/{document_id}/versions", response_model=DocumentVersionReadDTO, status_code=status.HTTP_201_CREATED)
async def create_document_version(
    document_id: UUID,
    version: DocumentVersionCreateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await create_document_version_service(db, current_user, document_id, version)


@router.post("/{document_id}/submit", response_model=DocumentReadDTO)
async def submit_document(
    document_id: UUID,
    payload: DocumentSubmitDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await submit_document_service(db, current_user, document_id, payload)


@router.post("/{document_id}/approve", response_model=DocumentReadDTO)
async def approve_document(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await approve_document_service(db, current_user, document_id)


@router.post("/{document_id}/reject", response_model=DocumentReadDTO)
async def reject_document(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    document_id: UUID,
    comment: str = Body(..., embed=True),
):
    return await reject_document_service(db, current_user, document_id, comment)


@router.post("/{document_id}/versions", response_model=DocumentVersionReadDTO, status_code=status.HTTP_201_CREATED)
async def upload_document_version(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_session)],
    document_id: UUID,
    file: UploadFile = File(...),

    
):
    return await upload_document_version_service(db, current_user, document_id, file)


@router.get("/{document_id}/versions/{version_id}/download")
async def download_document_version(
    document_id: UUID,
    version_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    version = await DocumentRepository.get_document_version(document_id, version_id, db)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if version.document.author_id != current_user.user_id and version.document.status_id != 1:
        raise HTTPException(status_code=403, detail="Access denied")

    stream = get_minio_object_stream(version.storage_object_name)
    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{version.original_file_name.rsplit(".", 1)[0]}.pdf"'
        },
    )


@router.get("/{document_id}/versions/{version_id}/download-url")
async def get_document_download_url(
    document_id: UUID,
    version_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    version = await DocumentRepository.get_document_version(document_id, version_id, db)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if version.document.author_id != current_user.user_id and version.document.status_id != 1:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"url": get_presigned_download_url(version.storage_object_name)}