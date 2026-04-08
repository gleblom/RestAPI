from uuid import UUID
import uuid

from models.documents import Document, DocumentApproval, DocumentUnit, DocumentVersion

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.views import MVDocument, MVDocumentApproval, MVDocumentVersion


class DocumentRepository:
    
    @staticmethod
    async def create_document(document: Document, db: AsyncSession) -> Document:
        db.add(document)
        
        await db.flush()
        
        return document
    
    @staticmethod
    async def get_documents_by_user(user_id: UUID, db: AsyncSession):
        result = await db.execute(select(Document).where(Document.author_id == user_id))
        
        return result.all()
    
    @staticmethod
    async def get_document_id(document_id: UUID, db: AsyncSession) -> Document | None:
        result = await db.execute(select(Document).where(Document.id == document_id))
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_public_documents_by_unit(unit_id: int, db: AsyncSession):
        result = await db.execute(
            select(MVDocument)
            .where(and_(MVDocument.unit_id == unit_id, MVDocument.status_id == 1)))
        
        return result.all()
    
    @staticmethod
    async def delete_document(document: Document, db: AsyncSession):
       await db.delete(document)
       await db.flush()
    
    @staticmethod
    async def update_document(doc_data: dict, document: Document, db:AsyncSession):
        
        for k, v in doc_data.items():
            setattr(document, k, v)
            
        await db.flush()
        
        return document
        
    @staticmethod
    async def create_document_approval(approval: DocumentApproval, db: AsyncSession):
        
        db.add(approval)
        
        await db.flush()
        
        return approval
    
    @staticmethod
    async def get_approvals_by_doc(document_id: UUID, db: AsyncSession):
        result = await db.execute(select(MVDocumentApproval).where(MVDocumentApproval.document_id == document_id))
        
        return result.all()
    
    @staticmethod
    async def create_document_version(version: DocumentVersion, db: AsyncSession):
        db.add(version)
        
        await db.flush()
        
        return version

    @staticmethod
    async def get_document_versions(document_id: UUID, db: AsyncSession):
        result = await db.execute(select(MVDocumentVersion).where(MVDocumentVersion.document_id == document_id))
        
        return result.all()
    
    @staticmethod
    async def create_document_unit(doc_unit: DocumentUnit, db: AsyncSession):
        db.add(doc_unit)
        
        await db.flush()
        
        return doc_unit
        