from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config.main import Config
from database import get_session
from models.dictionaries import UnitCompany
from models.documents import Document, DocumentUnit, DocumentVersion
from repositories.document_repository import DocumentRepository
from schemas.documents import DocumentCreateDTO, DocumentVersionCreateDTO
from security import CurrentUser

from minio import Minio

from services.document_storage_service import upload_document_version_to_storage

PUBLISHED_STATUS_ID = 1
DRAFT_STATUS_ID = 2
IN_PROGRESS_STATUS_ID = 3
RETURNED_STATUS_ID = 4

settings = Config() # type: ignore




async def create_document_service(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    document: DocumentCreateDTO,
):
    if document.unit_id != current_user.unit_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to create a document in another unit",
        )

    try:
        new_document = Document(
            title=document.title.strip(),
            current_step_index=0,
            expires_at=document.expires_at,
            category_id=document.category_id,
            status_id=DRAFT_STATUS_ID,
            author_id=current_user.user_id,
            route_id=None,
            doc_unit_id=None,
        )
        created_document = await DocumentRepository.create_document(new_document, db)

        doc_unit = await DocumentRepository.create_document_unit(
            DocumentUnit(
                document_id=created_document.id,
                unit_id=current_user.unit_id,
            ),
            db,
        )

        created_document.doc_unit_id = doc_unit.id
        await db.flush()
        await db.commit()
        await db.refresh(created_document)
        return created_document
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating document",
        ) from e

async def get_document_service(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    document_id: UUID,
):
    document = await DocumentRepository.get_document_by_id(document_id, db)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    is_author = document.author_id == current_user.user_id
    is_published = document.status_id == PUBLISHED_STATUS_ID

    accessible_units = await db.execute(
        select(DocumentUnit.unit_id)
        .join(UnitCompany, UnitCompany.unit_id == DocumentUnit.unit_id)
        .where(
            DocumentUnit.document_id == document_id,
            UnitCompany.company_id == current_user.company_id,
        )
    )
    accessible_unit_ids = set(accessible_units.scalars().all())

    if not (is_author or is_published or current_user.unit_id in accessible_unit_ids):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Document is not available")

    return document

async def create_document_version_service(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    document_id: UUID,
    version: DocumentVersionCreateDTO,
):
    document = await DocumentRepository.get_document_by_id(document_id, db)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.author_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can upload a new version")

    try:
        next_version_number = version.version_number or await DocumentRepository.get_next_document_version_number(document_id, db)

        created_version = await DocumentRepository.create_document_version(
            DocumentVersion(
                document_id=document_id,
                version_number=next_version_number,
                url=version.url,
            ),
            db,
        )

        document.status_id = DRAFT_STATUS_ID
        document.current_step_index = 0
        await db.flush()
        await db.commit()
        await db.refresh(created_version)
        return created_version
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating document version",
        ) from e


async def list_documents_service(
    db: AsyncSession,
    current_user: CurrentUser,
    status_id: int | None = None,
    category_id: int | None = None,
    search: str | None = None,
    mode: str | None = None,
):
    return await DocumentRepository.get_documents(
        db,
        user_id=cast(UUID, current_user.user_id),
        unit_id=current_user.unit_id,
        status_id=status_id,
        category_id=category_id,
        search=search,
        mode=mode,
    )

async def upload_document_version_service(
    db: AsyncSession,
    current_user: CurrentUser,
    document_id,
    upload: UploadFile,
):
    document = await DocumentRepository.get_document_by_id(document_id, db)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.author_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can upload a new version")

    storage_meta = await upload_document_version_to_storage(db, document_id, upload)

    try:
        version = await DocumentRepository.create_document_version(
            DocumentVersion(
                document_id=document_id,
                version_number=storage_meta["version_number"],
                storage_object_name=storage_meta["storage_object_name"],
                original_file_name=storage_meta["original_file_name"],
                mime_type=storage_meta["mime_type"],
                file_size=storage_meta["file_size"],
            ),
            db,
        )
        await db.commit()
        await db.refresh(version)
        return version
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while saving document version") from e
        
    