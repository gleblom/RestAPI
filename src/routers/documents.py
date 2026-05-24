from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.approvals import DocumentApprovalReadDTO
from src.database import get_session
from src.repositories.document_repository import DocumentRepository
from src.schemas.documents import (
    DocumentCreateDTO,
    DocumentReadDTO,
    DocumentSubmitDTO,
    DocumentVersionCreateDTO,
    DocumentVersionReadDTO,
)
from src.security import CurrentUser
from src.services.approval_service import approve_document_service, reject_document_service, submit_document_service
from src.services.document_service import (
    create_document_service,
    create_document_units_service,
    create_document_version_service,
    get_document_approval_service,
    get_document_approvals_service,
    get_document_service,
    get_document_versions_service,
    list_documents_service,
    upload_document_version_service,
)
from src.services.document_storage_service import get_minio_object_stream, get_presigned_download_url

router = APIRouter(prefix="/documents", tags=["documents"])



@router.get("/")
async def list_documents(
    current_user: CurrentUser,
    status_id: Annotated[list[int] | None, Query()] = None,
    category_id: Annotated[list[int] | None, Query()] = None,
    search: str | None = None,
    mode: str | None = None,
    authors: Annotated[list[UUID] | None, Query()] = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: AsyncSession = Depends(get_session),
):

    
    return await list_documents_service(
        db,
        current_user,
        status_id,
        category_id,
        search,
        mode,
        authors=authors,
        from_date=from_date,
        to_date=to_date
        
    )
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


@router.post("/{document_id}/versions/create", response_model=DocumentVersionReadDTO, status_code=status.HTTP_201_CREATED)
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


@router.post("/{document_id}/versions/upload", response_model=DocumentVersionReadDTO, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=404, detail="Not found")
    
    is_author = version.document.author_id == current_user.user_id
    is_published = version.document.status_id == 1
    is_approver = current_user.user_id in [a.approver_id for a in version.document.approvals]

    if not (is_author or is_published or is_approver):
        raise HTTPException(status_code=404, detail="Not found")
    

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


    return {"url": get_presigned_download_url(version.storage_object_name)}

@router.get("/{document_id}/versions")
async def get_document_versions(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser
):
    return await get_document_versions_service(db, current_user, document_id)

@router.get("/{document_id}/approvals")
async def get_document_approvals(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser
):
    return await get_document_approvals_service(db, current_user, document_id)


@router.get("/{document_id}/versions/{version_id}/approval/{step_index}", response_model=DocumentApprovalReadDTO)
async def get_approval_by_step(
    document_id: UUID,
    step_index: int,
    version_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser
):
    return await get_document_approval_service(db, current_user, document_id, version_id, step_index)

@router.post("/{document_id}/units")
async def create_document_units(
    document_id: UUID,
    request: Request,
    unit_ids: list[int],
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser
):
    print(request.body)
    return await create_document_units_service(current_user, db, unit_ids, document_id)
    
