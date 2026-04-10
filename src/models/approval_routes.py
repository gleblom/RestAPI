from sqlalchemy import UUID, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class ApprovalRoute(Base):
    __tablename__ = "approval_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    created_by: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    company_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))

    creator = relationship("User", back_populates="created_routes")
    company = relationship("Company", back_populates="routes")
    documents = relationship("Document", back_populates="route")

    nodes = relationship("RouteNode", back_populates="route", cascade="all, delete-orphan")
    edges = relationship("RouteEdge", back_populates="route", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ApprovalRoute(id={self.id}, name={self.name}, created_by={self.created_by})>"

class RouteNode(Base):
    __tablename__ = "route_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("approval_routes.id", ondelete="CASCADE"), nullable=False)
    approver_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    step_index: Mapped[int] = mapped_column(Integer, nullable=False)

    route = relationship("ApprovalRoute", back_populates="nodes")
    approver = relationship("User", back_populates="route_nodes")

    outgoing_edges = relationship("RouteEdge",foreign_keys="RouteEdge.from_node_id",back_populates="from_node")

    incoming_edges = relationship("RouteEdge", foreign_keys="RouteEdge.to_node_id", back_populates="to_node")

    __table_args__ = (
        UniqueConstraint("route_id" , "step_index"),
    )
    
    def __repr__(self):
        return f"<RouteNode(id={self.id}, route_id={self.route_id}, approver_id={self.approver_id}, step_index={self.step_index})>"

class RouteEdge(Base):
    __tablename__ = "route_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("approval_routes.id", ondelete="CASCADE"), nullable=False)
    from_node_id: Mapped[int] = mapped_column(Integer, ForeignKey("route_nodes.id", ondelete="CASCADE"), nullable=False)
    to_node_id: Mapped[int] = mapped_column(Integer, ForeignKey("route_nodes.id", ondelete="CASCADE"), nullable=False)

    route = relationship("ApprovalRoute", back_populates="edges")

    from_node = relationship("RouteNode",foreign_keys=[from_node_id],back_populates="outgoing_edges")
    to_node = relationship("RouteNode", foreign_keys=[to_node_id], back_populates="incoming_edges")
    
    
    def __repr__(self):
        return f"<RouteEdge(id={self.id}, route_id={self.route_id}, from_node_id={self.from_node_id}, to_node_id={self.to_node_id})>"