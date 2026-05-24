from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApprovalRouteCreateDTO(BaseModel): # @IgnoreException
    name: str


class ApprovalRouteUpdateDTO(BaseModel): # @IgnoreException
    name: Optional[str] = None


class ApprovalRouteReadDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: UUID
    company_id: UUID


class RouteNodeCreateDTO(BaseModel): # @IgnoreException
    approver_id: UUID
    step_index: int


class RouteNodeUpdateDTO(BaseModel): # @IgnoreException
    approver_id: Optional[UUID] = None
    step_index: Optional[int] = None


class RouteNodeReadDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: int
    approver_id: UUID
    step_index: int


class RouteEdgeCreateDTO(BaseModel): # @IgnoreException
    from_node_id: int
    to_node_id: int


class RouteEdgeReadDTO(BaseModel): # @IgnoreException
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: int
    from_node_id: int
    to_node_id: int


class RouteGraphNodeDTO(BaseModel): # @IgnoreException
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


class RouteGraphEdgeDTO(BaseModel): # @IgnoreException
    id: int
    route_id: int
    from_node_id: int
    to_node_id: int


class RouteGraphDTO(BaseModel): # @IgnoreException
    route: ApprovalRouteReadDTO
    nodes: list[RouteGraphNodeDTO]
    edges: list[RouteGraphEdgeDTO]
    levels: list[list[int]]