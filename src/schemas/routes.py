from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApprovalRouteCreateDTO(BaseModel):
    name: str


class ApprovalRouteUpdateDTO(BaseModel):
    name: Optional[str] = None


class ApprovalRouteReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: UUID
    company_id: UUID


class RouteNodeCreateDTO(BaseModel):
    approver_id: UUID
    step_index: int


class RouteNodeUpdateDTO(BaseModel):
    approver_id: Optional[UUID] = None
    step_index: Optional[int] = None


class RouteNodeReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: int
    approver_id: UUID
    step_index: int


class RouteEdgeCreateDTO(BaseModel):
    from_node_id: int
    to_node_id: int


class RouteEdgeReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: int
    from_node_id: int
    to_node_id: int


class RouteGraphNodeDTO(BaseModel):
    id: int
    route_id: int
    approver_id: UUID
    approver_email: Optional[str] = None
    approver_full_name: Optional[str] = None
    step_index: int
    incoming_count: int
    outgoing_count: int
    is_start: bool
    is_terminal: bool
    level: int


class RouteGraphEdgeDTO(BaseModel):
    id: int
    route_id: int
    from_node_id: int
    to_node_id: int


class RouteGraphDTO(BaseModel):
    route: ApprovalRouteReadDTO
    nodes: list[RouteGraphNodeDTO]
    edges: list[RouteGraphEdgeDTO]
    levels: list[list[int]]