from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.documents import Document, DocumentApproval, DocumentUnit, DocumentVersion, Notification
from src.models.views import MVDocument, MVDocumentApproval, MVDocumentVersion


class DocumentRepository:
    @staticmethod
    async def create_document(document: Document, db: AsyncSession) -> Document:
        db.add(document)
        await db.flush()
        return document

    @staticmethod
    async def get_document_by_id(document_id: UUID, db: AsyncSession) -> Document | None:
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_public_documents_by_unit(unit_id: int, db: AsyncSession):
        result = await db.execute(
            select(MVDocument).where(and_(MVDocument.unit_id == unit_id, MVDocument.status_id == 1))
        )
        return result.scalars().all()

    @staticmethod
    async def delete_document(document: Document, db: AsyncSession):
        await db.delete(document)
        await db.flush()

    @staticmethod
    async def update_document(doc_data: dict, document: Document, db: AsyncSession):
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
        return result.scalars().all()

    @staticmethod
    async def get_latest_document_version(document_id: UUID, db: AsyncSession) -> DocumentVersion | None:
        result = await db.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(desc(DocumentVersion.version_number), desc(DocumentVersion.id))
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_document_approval_by_step(
        *,
        document_id: UUID,
        version_id: int,
        step_index: int,
        db: AsyncSession,
    ) -> DocumentApproval | None:
        result = await db.execute(
            select(DocumentApproval).where(
                and_(
                    DocumentApproval.document_id == document_id,
                    DocumentApproval.version_id == version_id,
                    DocumentApproval.step_index == step_index,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_document_version(version: DocumentVersion, db: AsyncSession):
        db.add(version)
        await db.flush()
        return version

    @staticmethod
    async def get_document_versions(document_id: UUID, db: AsyncSession):
        result = await db.execute(select(MVDocumentVersion).where(MVDocumentVersion.document_id == document_id))
        return result.scalars().all()

    @staticmethod
    async def get_next_document_version_number(document_id: UUID, db: AsyncSession) -> int:
        result = await db.execute(
            select(func.coalesce(func.max(DocumentVersion.version_number), 0)).where(
                DocumentVersion.document_id == document_id
            )
        )
        return int(result.scalar_one()) + 1

    @staticmethod
    async def create_document_unit(doc_unit: DocumentUnit, db: AsyncSession):
        db.add(doc_unit)
        await db.flush()
        return doc_unit

    @staticmethod
    async def get_document_unit_ids(document_id: UUID, db: AsyncSession):
        result = await db.execute(
            select(DocumentUnit.unit_id).where(DocumentUnit.document_id == document_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_documents(
        db: AsyncSession,
        *,
        user_id: UUID,
        unit_id: int,
        status_id: list[int]  | None = None,
        category_id: list[int]  | None = None,
        search: str | None = None,
        mode: str | None = None, 
        authors: list[UUID] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None
    ):
        query = select(MVDocument)

        conditions = []

        if mode == "my":
            conditions.append(MVDocument.author_id == user_id)

        elif mode == "all":
            conditions.append(MVDocument.status_id == 1)
            query = select(MVDocument).join(DocumentUnit, DocumentUnit.document_id == MVDocument.document_id).where(DocumentUnit.unit_id == unit_id).distinct()
        elif mode == "incoming":
            query = select(MVDocument).join(Notification, Notification.document_id == MVDocument.document_id).where(Notification.user_id == user_id)

        else:
            conditions.append(MVDocument.unit_id == unit_id)

        if status_id:
            conditions.append(MVDocument.status_id.in_(status_id))

        if category_id:
            conditions.append(MVDocument.category_id.in_(category_id))
        if authors:
            conditions.append(MVDocument.author_id.in_(authors))
        if search:
            conditions.append(MVDocument.title.ilike(f"%{search}%"))
        if from_date:
            conditions.append(MVDocument.created_at.between(from_date, to_date))
        if to_date:
            conditions.append(MVDocument.created_at.between(from_date, to_date))
        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        return result.scalars().all()
    

    @staticmethod
    async def get_document_version(document_id: UUID, version_id: int, db: AsyncSession) -> DocumentVersion | None:
        result = await db.execute(select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id,
                   DocumentVersion.id == version_id,)
        .options(selectinload(DocumentVersion.document)
            .selectinload(Document.approvals)))
        return result.scalar_one_or_none()
            
