import uuid

from sqlalchemy import UUID, DateTime, Index, Integer, String, Boolean, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title: Mapped[str] = mapped_column(String, nullable=False)
    current_step_index: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("approval_routes.id"), nullable=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"))
    status_id: Mapped[int] = mapped_column(Integer, ForeignKey("statuses.id"))
    author_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    route = relationship("ApprovalRoute", back_populates="documents")
    category = relationship("Category", back_populates="documents")
    status = relationship("Status", back_populates="documents")
    author = relationship("User", back_populates="documents")

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    approvals = relationship("DocumentApproval", back_populates="document")

    document_units = relationship("DocumentUnit", back_populates="document")

    __table_args__ = (
        Index("ix_documents_search", "status_id", "category_id", "created_at"),
    )
     
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title}, author_id={self.author_id}, created_at={self.created_at})>"

class DocumentUnit(Base):
    __tablename__ = "document_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)

    document = relationship("Document", back_populates="document_units")
    unit = relationship("Unit", back_populates="document_units")

    __table_args__ = (
        UniqueConstraint("document_id", "unit_id"),
    )
    
    def __repr__(self):
        return f"<DocumentUnit(id={self.id}, document_id={self.document_id}, unit_id={self.unit_id})>"

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    storage_object_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    original_file_name: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False, default="application/pdf")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="versions")
    approvals = relationship("DocumentApproval", back_populates="version")

    __table_args__ = (
        UniqueConstraint("document_id", "version_number"),
    )
    
    def __repr__(self):
        return f"<DocumentVersion(id={self.id}, document_id={self.document_id}, version_number={self.version_number}, created_at={self.created_at})>"

class DocumentApproval(Base):
    __tablename__ = "document_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    approver_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=True)
    comment: Mapped[str] = mapped_column(String, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    version = relationship("DocumentVersion", back_populates="approvals")
    document = relationship("Document", back_populates="approvals")
    approver = relationship("User", back_populates="document_approvals")

    __table_args__ = (
        Index("ix_doc_approval_step", "version_id", "step_index"),
    )
    
    def __repr__(self):
        return f"<DocumentApproval(id={self.id}, version_id={self.version_id}, approver_id={self.approver_id}, step_index={self.step_index}, is_approved={self.is_approved})>"

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    message: Mapped[str] = mapped_column(String, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="notifications")
    document = relationship("Document")

    __table_args__ = (
        Index("ix_notifications_user", "user_id", "is_read"),
    )
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, message={self.message}, is_read={self.is_read}, created_at={self.created_at})>"