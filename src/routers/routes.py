from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.routes import (
    ApprovalRouteCreateDTO,
    ApprovalRouteReadDTO,
    ApprovalRouteUpdateDTO,
    RouteEdgeCreateDTO,
    RouteEdgeReadDTO,
    RouteGraphDTO,
    RouteNodeCreateDTO,
    RouteNodeReadDTO,
    RouteNodeUpdateDTO,
)
from security import CurrentUser
from services.route_service import (
    add_edge_service,
    add_node_service,
    create_route_service,
    delete_edge_service,
    delete_node_service,
    delete_route_service,
    get_route_graph_service,
    get_route_service,
    list_routes_service,
    update_node_service,
    update_route_service,
)

router = APIRouter(prefix="/approval-routes", tags=["approval-routes"])


@router.post("", response_model=ApprovalRouteReadDTO, status_code=status.HTTP_201_CREATED)
async def create_route(
    payload: ApprovalRouteCreateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await create_route_service(db, current_user, payload)


@router.get("", response_model=list[ApprovalRouteReadDTO])
async def list_routes(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await list_routes_service(db, current_user)


@router.get("/{route_id}", response_model=ApprovalRouteReadDTO)
async def get_route(
    route_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await get_route_service(db, current_user, route_id)


@router.put("/{route_id}", response_model=ApprovalRouteReadDTO)
async def update_route(
    route_id: int,
    payload: ApprovalRouteUpdateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await update_route_service(db, current_user, route_id, payload)


@router.delete("/{route_id}", status_code=status.HTTP_200_OK)
async def delete_route(
    route_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await delete_route_service(db, current_user, route_id)


@router.post("/{route_id}/nodes", response_model=RouteNodeReadDTO, status_code=status.HTTP_201_CREATED)
async def create_node(
    route_id: int,
    payload: RouteNodeCreateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await add_node_service(db, current_user, route_id, payload)


@router.put("/{route_id}/nodes/{node_id}", response_model=RouteNodeReadDTO)
async def update_node(
    route_id: int,
    node_id: int,
    payload: RouteNodeUpdateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await update_node_service(db, current_user, route_id, node_id, payload)


@router.delete("/{route_id}/nodes/{node_id}", status_code=status.HTTP_200_OK)
async def delete_node(
    route_id: int,
    node_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await delete_node_service(db, current_user, route_id, node_id)


@router.post("/{route_id}/edges", response_model=RouteEdgeReadDTO, status_code=status.HTTP_201_CREATED)
async def create_edge(
    route_id: int,
    payload: RouteEdgeCreateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await add_edge_service(db, current_user, route_id, payload)


@router.delete("/{route_id}/edges/{edge_id}", status_code=status.HTTP_200_OK)
async def delete_edge(
    route_id: int,
    edge_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await delete_edge_service(db, current_user, route_id, edge_id)


@router.get("/{route_id}/graph", response_model=RouteGraphDTO)
async def get_route_graph(
    route_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await get_route_graph_service(db, current_user, route_id)