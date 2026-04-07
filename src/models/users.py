import uuid

from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column (Boolean, default=False, nullable=False)

    company_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    company = relationship("Company", back_populates="users")

    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    created_routes = relationship("ApprovalRoute", back_populates="creator")
    documents = relationship("Document", back_populates="author")

    route_nodes = relationship("RouteNode", back_populates="approver")
    document_approvals = relationship("DocumentApproval", back_populates="approver")

    notifications = relationship("Notification", back_populates="user")
    
    
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active}, is_email_verified={self.is_email_verified})>"
    
class UserToken(Base):
    __tablename__ = "user_tokens"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    token_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    token_type: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="tokens")

    __table_args__ = (
        Index("ix_user_tokens_user_expires", "user_id", "expires_at"),
    )
    
    def __repr__(self):
        return f"<UserToken(id={self.id}, user_id={self.user_id}, created_at={self.created_at}, expires_at={self.expires_at})>"

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    token_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    issued_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user", "user_id", "is_revoked"),
    )
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, issued_at={self.issued_at}, expires_at={self.expires_at}, is_revoked={self.is_revoked})>"

class Profile(Base):
    __tablename__ = "profiles"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    second_name: Mapped[str] = mapped_column(String, nullable=True)
    third_name: Mapped[str] = mapped_column(String, nullable=True)
    
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.id"), nullable=True)
    company_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    
    user = relationship("User", back_populates="profile")
    role = relationship("Role", back_populates="profiles")
    unit = relationship("Unit", back_populates="profiles")
    company = relationship("Company", back_populates="profiles")
    
    def __repr__(self):
        return f"<Profile(id={self.id}, first_name={self.first_name}, second_name={self.second_name}, third_name={self.third_name})>"