from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from exceptions import AlreadyExists, NotFound
from models.documents import Document
from repositories.document_repository import DocumentRepository
from schemas.documents import DocumentCreateDTO, DocumentUpdateDTO
from security import CurrentUser

async def create_document_service(
    db: Annotated[AsyncSession, Depends(get_session)], 
    current_user: CurrentUser,
    document: DocumentCreateDTO
    ):
    
    if document.unit_id != current_user.unit_id:
        raise
    
    try:
        new_document = Document(
            title = document.title,
            current_step_index = 0,
            expires_at = document.expires_at,
            category_id = document.category_id,
            status_id = 1,
            author_id = current_user.user_id
        )
        
        created_document = await DocumentRepository.create_document(new_document, db)
        
        await db.commit()
        await db.refresh(created_document)
        
        return created_document
    
    except Exception as e:
        await db.rollback()
        raise e
