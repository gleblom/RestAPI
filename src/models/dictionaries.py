import uuid

from sqlalchemy import UUID, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class Role(Base):
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    company_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    
    profiles = relationship("Profile", back_populates="role")
    role_category = relationship("RoleCategory", back_populates="role", cascade="all, delete-orphan")
    company = relationship("Company", back_populates="roles")
    
    def __repr__(self): 
        return f"<Role(id={self.id}, name={self.name})>"
    
class RoleCategory(Base):
    __tablename__ = "role_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    role = relationship("Role", back_populates="role_categories")
    category = relationship("Category", back_populates="role_categories")

    __table_args__ = (
        UniqueConstraint("role_id", "category_id"),
    )
    
    def __repr__(self):
        return f"<RoleCategory(id={self.id}, role_id={self.role_id}, category_id={self.category_id})>"

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    role_categories = relationship("RoleCategory", back_populates="category")
    documents = relationship("Document", back_populates="category")
    
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"
    


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)

    director_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    users = relationship("User", back_populates="company")
    routes = relationship("ApprovalRoute", "company")
    profiles = relationship("Profile", back_populates="company")

    roles = relationship("Role", back_populates="company")
    unit_companies = relationship("UnitCompany", back_populates="company")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name})>"

class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    profiles = relationship("Profile", back_populates="unit")
    unit_companies = relationship("UnitCompany", back_populates="unit")
    document_units = relationship("DocumentUnit", back_populates="unit")
    
    def __repr__(self):
        return f"<Unit(id={self.id}, name={self.name})>"

class UnitCompany(Base):
    __tablename__ = "unit_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    unit = relationship("Unit", back_populates="unit_companies")
    company = relationship("Company", back_populates="unit_companies")

    __table_args__ = (
        UniqueConstraint("unit_id", "company_id"),
    )
    
    def __repr__(self):
        return f"<UnitCompany(id={self.id}, unit_id={self.unit_id}, company_id={self.company_id})>"

class Status(Base):
    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    documents = relationship("Document", back_populates="status")
    
    def __repr__(self):
        return f"<Status(id={self.id}, name={self.name})>"
    