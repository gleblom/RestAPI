from sqlalchemy import UUID, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

class MVDocument(Base):
    __tablename__ = "mv_documents_full"

    document_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    title: Mapped[str] = mapped_column(String)
    current_step_index: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))

    status_id: Mapped[int] = mapped_column(Integer)
    status_name : Mapped[str] = mapped_column(String)

    category_id: Mapped[int] = mapped_column(Integer)
    category_name : Mapped[str] = mapped_column(String)

    author_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    author_email: Mapped[str] = mapped_column(String)
    
    unit_id: Mapped[int] = mapped_column(Integer)
    unit_name: Mapped[int] = mapped_column(Integer)
    
    first_name: Mapped[str] = mapped_column(String)
    second_name: Mapped[str] = mapped_column(String)
    second_name: Mapped[str] = mapped_column(String)
    third_name: Mapped[str] = mapped_column(String)

    route_id: Mapped[int] = mapped_column(Integer)
    route_name : Mapped[str] = mapped_column(String)

    latest_version_id: Mapped[int] = mapped_column(Integer)
    latest_version_number: Mapped[int] = mapped_column(Integer)
    latest_version_url : Mapped[str] = mapped_column(String)


    def __repr__(self):
        return f"<MVDocument(id={self.document_id}, title={self.title})>"

class MVDocumentApproval(Base):
    __tablename__ = "mv_document_approvals"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    version_id: Mapped[int] = mapped_column(Integer)
    document_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))

    title : Mapped[str] = mapped_column(String)
    version_number: Mapped[int] = mapped_column(Integer)

    approver_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    approver_email : Mapped[str] = mapped_column(String)

    step_index: Mapped[int] = mapped_column(Integer)
    is_approved: Mapped[bool] = mapped_column(Boolean)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"<MVApproval(id={self.id}, document_id={self.document_id}, step={self.step_index})>"

class MVRoute(Base):
    __tablename__ = "mv_routes"

    route_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name : Mapped[str] = mapped_column(String)
    created_by: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    creator_email : Mapped[str] = mapped_column(String)
    
    company_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))

    nodes_count: Mapped[int] = mapped_column(Integer)
    edges_count: Mapped[int] = mapped_column(Integer)

    def __repr__(self):
        return f"<MVRoute(id={self.route_id}, name={self.name})>"
    
class MVDocumentVersion(Base):
    __tablename__ = "mv_document_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    document_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    title : Mapped[str] = mapped_column(String)

    version_number: Mapped[int] = mapped_column(Integer)
    url : Mapped[str] = mapped_column(String)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))

    author_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    author_email : Mapped[str] = mapped_column(String)

    def __repr__(self):
        return f"<MVDocVersion(id={self.id}, doc={self.document_id}, v={self.version_number})>"

class MVNotification(Base):
    __tablename__ = "mv_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    email : Mapped[str] = mapped_column(String)

    document_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    document_title : Mapped[str] = mapped_column(String)

    message : Mapped[str] = mapped_column(String)
    is_read: Mapped[bool] = mapped_column(Boolean)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"<MVNotification(id={self.id}, user={self.user_id}, read={self.is_read})>"
    
class VUser(Base):
    __tablename__ = "v_users_full"
    
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    
    user_email : Mapped[str] = mapped_column(String)
    user_phone: Mapped[str] = mapped_column(String)
    
    is_active: Mapped[bool] = mapped_column(Boolean)
    is_email_verified: Mapped[bool] = mapped_column(Boolean)
    
    user_created_add: Mapped[bool] = mapped_column(Boolean)
    user_updated_at: Mapped[bool] = mapped_column(Boolean)
    
    first_name: Mapped[str] = mapped_column(String)
    second_name: Mapped[str] = mapped_column(String)
    third_name: Mapped[str] = mapped_column(String)
    
    company_id:  Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    company_name: Mapped[str] = mapped_column(String)
    
    role_id:Mapped[int] = mapped_column(Integer)
    role_name: Mapped[str] = mapped_column(String)
        
    unit_id:Mapped[int] = mapped_column(Integer)
    unit_name: Mapped[str] = mapped_column(String)

class VRoleCategory(Base):
    __tablename__ = "v_role_categories_full"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    role_id:Mapped[int] = mapped_column(Integer)
    role_name: Mapped[str] = mapped_column(String)
    
    category_id:Mapped[int] = mapped_column(Integer)
    category_name: Mapped[str] = mapped_column(String)
    
    company_id:  Mapped[UUID] = mapped_column(UUID(as_uuid=True))