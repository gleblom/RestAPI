from __future__ import annotations

from collections import defaultdict, deque
from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval_routes import ApprovalRoute, RouteEdge, RouteNode
from repositories.route_repository import RouteRepository
from schemas.routes import (
    ApprovalRouteCreateDTO,
    ApprovalRouteReadDTO,
    ApprovalRouteUpdateDTO,
    RouteEdgeCreateDTO,
    RouteGraphDTO,
    RouteGraphEdgeDTO,
    RouteGraphNodeDTO,
    RouteNodeCreateDTO,
    RouteNodeUpdateDTO,
)
from security import CurrentUser


def _ensure_same_company(route_company_id: UUID, current_company_id: UUID) -> None:
    if route_company_id != current_company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _toposort_levels(nodes: list[RouteNode], edges: list[RouteEdge]) -> list[list[int]]:
    graph = defaultdict(list)
    indegree = {node.id: 0 for node in nodes}

    for edge in edges:
        graph[edge.from_node_id].append(edge.to_node_id)
        indegree[edge.to_node_id] = indegree.get(edge.to_node_id, 0) + 1

    queue = deque(sorted([nid for nid, deg in indegree.items() if deg == 0]))
    levels: list[list[int]] = []

    while queue:
        current_level_size = len(queue)
        level: list[int] = []

        for _ in range(current_level_size):
            node_id = queue.popleft()
            level.append(node_id)

            for next_id in sorted(graph[node_id]):
                indegree[next_id] -= 1
                if indegree[next_id] == 0:
                    queue.append(next_id)

        levels.append(level)

    return levels


def _validate_acyclic(nodes: list[RouteNode], edges: list[RouteEdge]) -> None:
    levels = _toposort_levels(nodes, edges)
    if sum(len(level) for level in levels) != len(nodes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Route graph contains a cycle or disconnected back-edge",
        )


async def create_route_service(db: AsyncSession, current_user: CurrentUser, payload: ApprovalRouteCreateDTO):
    try:
        route = await RouteRepository.create_route(
            ApprovalRoute(
                name=payload.name.strip(),
                created_by=current_user.user_id,
                company_id=current_user.company_id,
            ),
            db,
        )
        await db.commit()
        await db.refresh(route)
        return route
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while creating route") from e


async def list_routes_service(db: AsyncSession, current_user: CurrentUser):
    return await RouteRepository.list_routes(current_user.company_id, db)


async def get_route_service(db: AsyncSession, current_user: CurrentUser, route_id: int):
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))
    return route


async def update_route_service(db: AsyncSession, current_user: CurrentUser, route_id: int, payload: ApprovalRouteUpdateDTO):
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))

    try:
        if payload.name is not None:
            route.name = payload.name.strip()
        await db.commit()
        await db.refresh(route)
        return route
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while updating route") from e


async def delete_route_service(db: AsyncSession, current_user: CurrentUser, route_id: int):
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))

    try:
        await RouteRepository.delete_route(route, db)
        await db.commit()
        return {"detail": "Route deleted"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while deleting route") from e


async def add_node_service(db: AsyncSession, current_user: CurrentUser, route_id: int, payload: RouteNodeCreateDTO):
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))

    if any(node.step_index == payload.step_index for node in route.nodes):
        raise HTTPException(status_code=409, detail="Step index already exists in this route")

    try:
        node = await RouteRepository.create_node(
            RouteNode(route_id=route_id, approver_id=payload.approver_id, step_index=payload.step_index),
            db,
        )
        await db.commit()
        await db.refresh(node)
        return node
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while creating route node") from e


async def update_node_service(
    db: AsyncSession,
    current_user: CurrentUser,
    route_id: int,
    node_id: int,
    payload: RouteNodeUpdateDTO,
):
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))

    node = await RouteRepository.get_node(node_id, db)
    if not node or node.route_id != route_id:
        raise HTTPException(status_code=404, detail="Node not found")

    if payload.step_index is not None:
        if any(n.id != node.id and n.step_index == payload.step_index for n in route.nodes):
            raise HTTPException(status_code=409, detail="Step index already exists in this route")
        node.step_index = payload.step_index

    if payload.approver_id is not None:
        node.approver_id =  payload.approver_id  # type: ignore

    try:
        await db.commit()
        await db.refresh(node)
        return node
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while updating route node") from e


async def delete_node_service(db: AsyncSession, current_user: CurrentUser, route_id: int, node_id: int):
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))

    node = await RouteRepository.get_node(node_id, db)
    if not node or node.route_id != route_id:
        raise HTTPException(status_code=404, detail="Node not found")

    try:
        await RouteRepository.delete_node(node, db)
        await db.commit()
        return {"detail": "Node deleted"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while deleting route node") from e


async def add_edge_service(db: AsyncSession, current_user: CurrentUser, route_id: int, payload: RouteEdgeCreateDTO):
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))

    from_node = await RouteRepository.get_node(payload.from_node_id, db)
    to_node = await RouteRepository.get_node(payload.to_node_id, db)

    if not from_node or from_node.route_id != route_id:
        raise HTTPException(status_code=404, detail="from_node not found")
    if not to_node or to_node.route_id != route_id:
        raise HTTPException(status_code=404, detail="to_node not found")
    if from_node.id == to_node.id:
        raise HTTPException(status_code=400, detail="Self-loop is not allowed")
    if await RouteRepository.edge_exists(route_id, from_node.id, to_node.id, db):
        raise HTTPException(status_code=409, detail="Edge already exists")

    try:
        edge = await RouteRepository.create_edge(
            RouteEdge(route_id=route_id, from_node_id=from_node.id, to_node_id=to_node.id),
            db,
        )

        nodes = route.nodes
        edges = route.edges + [edge]
        _validate_acyclic(nodes, edges)

        await db.commit()
        await db.refresh(edge)
        return edge
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while creating route edge") from e


async def delete_edge_service(db: AsyncSession, current_user: CurrentUser, route_id: int, edge_id: int):
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))

    edge = await RouteRepository.get_edge(edge_id, db)
    if not edge or edge.route_id != route_id:
        raise HTTPException(status_code=404, detail="Edge not found")

    try:
        await RouteRepository.delete_edge(edge, db)
        await db.commit()
        return {"detail": "Edge deleted"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while deleting route edge") from e


async def get_route_graph_service(db: AsyncSession, current_user: CurrentUser, route_id: int) -> RouteGraphDTO:
    route = await RouteRepository.get_route(route_id, db)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    _ensure_same_company(cast(UUID, route.company_id), cast(UUID,current_user.company_id))

    nodes = sorted(route.nodes, key=lambda n: (n.step_index, n.id))
    edges = sorted(route.edges, key=lambda e: e.id)

    _validate_acyclic(nodes, edges)
    levels = _toposort_levels(nodes, edges)

    incoming = defaultdict(int)
    outgoing = defaultdict(int)
    for edge in edges:
        outgoing[edge.from_node_id] += 1
        incoming[edge.to_node_id] += 1

    level_by_node: dict[int, int] = {}
    for level_index, level in enumerate(levels):
        for node_id in level:
            level_by_node[node_id] = level_index

    graph_nodes = [
        RouteGraphNodeDTO(
            id=node.id,
            route_id=node.route_id,
            approver_id=node.approver_id,
            approver_email=node.approver.email if node.approver else None,
            approver_full_name=getattr(node.approver, "full_name", None) if node.approver else None,
            step_index=node.step_index,
            incoming_count=incoming[node.id],
            outgoing_count=outgoing[node.id],
            is_start=incoming[node.id] == 0,
            is_terminal=outgoing[node.id] == 0,
            level=level_by_node.get(node.id, 0),
        )
        for node in nodes
    ]

    graph_edges = [
        RouteGraphEdgeDTO(
            id=edge.id,
            route_id=edge.route_id,
            from_node_id=edge.from_node_id,
            to_node_id=edge.to_node_id,
        )
        for edge in edges
    ]
    
    approval_route = ApprovalRouteReadDTO(
        id = route.id,
        name = route.name,
        created_by=cast(UUID, route.created_by),
        company_id =cast(UUID, route.company_id),
    )

    return RouteGraphDTO(route=approval_route, nodes=graph_nodes, edges=graph_edges, levels=levels)