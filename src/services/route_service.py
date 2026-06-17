from __future__ import annotations

from collections import defaultdict, deque
from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.security import CurrentUser
from src.models.approval_routes import ApprovalRoute, RouteEdge, RouteNode
from src.repositories.route_repository import RouteRepository
from src.repositories.profile_repository import ProfileRepository
from src.schemas.routes import (
    ApprovalRouteCreateDTO,
    ApprovalRouteReadDTO,
    ApprovalRouteUpdateDTO,
    RouteEdgeCreateDTO,
    RouteGraphDTO,
    RouteGraphEdgeDTO,
    RouteGraphNodeDTO,
    RouteNodeCreateDTO,
    RouteNodeUpdateDTO,
    ApprovalRouteWithGraphCreateDTO,
    RouteEdgeByStepCreateDTO,
)
from types import SimpleNamespace
from src.security import CurrentUser


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


async def create_route_with_graph_service(
    db: AsyncSession,
    current_user: CurrentUser,
    payload: ApprovalRouteWithGraphCreateDTO,
):
    # basic validations
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="Route name is required")

    if not payload.nodes or len(payload.nodes) < 2:
        raise HTTPException(status_code=400, detail="Route must contain at least 2 steps")

    # unique step_index and approver checks
    seen_steps = set()
    seen_approvers = set()
    for n in payload.nodes:
        if n.step_index in seen_steps:
            raise HTTPException(status_code=409, detail="Step index already exists in this route")
        seen_steps.add(n.step_index)
        if n.approver_id in seen_approvers:
            raise HTTPException(status_code=409, detail="Approver already exists in this route")
        seen_approvers.add(n.approver_id)

    # Load and validate profiles/roles for nodes
    profiles_by_step: dict[int, object] = {}
    for n in payload.nodes:
        profile = await ProfileRepository.get_profile(n.approver_id, db)
        if not profile:
            raise HTTPException(status_code=404, detail="Approver not found")
        if profile.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Approver must belong to the same company as the route")
        if not profile.role:
            raise HTTPException(status_code=400, detail="Approver must have a role with level/sort_order")
        if profile.role.level == 90 and profile.role.sort_order == 1:
            raise HTTPException(status_code=400, detail="This role cannot be assigned to approval steps")
        profiles_by_step[n.step_index] = profile

    # disallow duplicate positions (level+sort_order)
    seen_positions = set()
    for step, profile in profiles_by_step.items():
        pos = (profile.role.level, profile.role.sort_order)
        if pos in seen_positions:
            raise HTTPException(status_code=409, detail="A role with this level and order already exists in the route")
        seen_positions.add(pos)

    # validate edges reference existing steps and no self-loops
    if not payload.edges:
        raise HTTPException(status_code=400, detail="Route must contain at least 1 edge")

    temp_nodes = [SimpleNamespace(id=s) for s in profiles_by_step.keys()]
    temp_edges = []
    for e in payload.edges:
        if e.from_step_index not in profiles_by_step or e.to_step_index not in profiles_by_step:
            raise HTTPException(status_code=404, detail="Route node not found")
        if e.from_step_index == e.to_step_index:
            raise HTTPException(status_code=400, detail="Self-loop is not allowed")
        temp_edges.append(SimpleNamespace(from_node_id=e.from_step_index, to_node_id=e.to_step_index))

    # acyclic check
    _validate_acyclic(temp_nodes, temp_edges)

    # sequential chain: indegree/outdegree must be <=1
    incoming = defaultdict(int)
    outgoing = defaultdict(int)
    for e in temp_edges:
        outgoing[e.from_node_id] += 1
        incoming[e.to_node_id] += 1

    for s in profiles_by_step.keys():
        if incoming[s] > 1 or outgoing[s] > 1:
            raise HTTPException(status_code=400, detail="Route must be strictly sequential (no branching allowed)")

    # role ordering per edge
    for e in temp_edges:
        ra = profiles_by_step[e.from_node_id].role
        rb = profiles_by_step[e.to_node_id].role
        if rb.level < ra.level or (rb.level == ra.level and rb.sort_order <= ra.sort_order):
            raise HTTPException(status_code=400, detail="Approver order must go from lower to higher (by level then sort_order)")

    # persist all in a single transaction
    try:
        route = ApprovalRoute(name=payload.name.strip(), created_by=current_user.user_id, company_id=current_user.company_id)
        route = await RouteRepository.create_route(route, db)

        # create nodes and map step_index -> node
        node_map: dict[int, RouteNode] = {}
        for n in payload.nodes:
            node = RouteNode(route_id=route.id, approver_id=n.approver_id, step_index=n.step_index)
            node = await RouteRepository.create_node(node, db)
            node_map[n.step_index] = node

        # create edges using created node ids
        for e in payload.edges:
            from_node = node_map[e.from_step_index]
            to_node = node_map[e.to_step_index]
            edge = RouteEdge(route_id=route.id, from_node_id=from_node.id, to_node_id=to_node.id)
            await RouteRepository.create_edge(edge, db)

        # commit all changes
        await db.commit()

        # transaction committed, fetch route graph and return
        return await get_route_graph_service(db, current_user, route.id)
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while creating route with graph") from e


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

    # do not allow deletion if route is in use by any documents
    if await RouteRepository.route_in_use(route.id, db):
        raise HTTPException(status_code=409, detail="Route is assigned to documents and cannot be deleted")

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

    if any(node.approver_id == payload.approver_id for node in route.nodes):
        raise HTTPException(status_code=409, detail="Approver already exists in this route")

    # load approver profile and role/unit info
    profile = await ProfileRepository.get_profile(payload.approver_id, db)
    if not profile:
        raise HTTPException(status_code=404, detail="Approver not found")
    if profile.company_id != route.company_id:
        raise HTTPException(status_code=403, detail="Approver must belong to the same company as the route")

    if not profile.role:
        raise HTTPException(status_code=400, detail="Approver must have a role with level/sort_order")

    # disallow roles that are administrative clerks/admins from being approvers (level 90, sort_order 1)
    if profile.role.level == 90 and profile.role.sort_order == 1:
        raise HTTPException(status_code=400, detail="This role cannot be assigned to approval steps")

    # disallow duplicate positions (same level and sort_order)
    for node in route.nodes:
        if node.approver and node.approver.profile and node.approver.profile.role:
            existing_role = node.approver.profile.role
            if existing_role.level == profile.role.level and existing_role.sort_order == profile.role.sort_order:
                raise HTTPException(status_code=409, detail="A role with this level and order already exists in the route")

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
        # check duplicate approver in route
        if any(n.id != node.id and n.approver_id == payload.approver_id for n in route.nodes):
            raise HTTPException(status_code=409, detail="Approver already exists in this route")

        profile = await ProfileRepository.get_profile(payload.approver_id, db)
        if not profile:
            raise HTTPException(status_code=404, detail="Approver not found")
        if profile.company_id != route.company_id:
            raise HTTPException(status_code=403, detail="Approver must belong to the same company as the route")
        if not profile.role:
            raise HTTPException(status_code=400, detail="Approver must have a role with level/sort_order")
        if profile.role.level == 90 and profile.role.sort_order == 1:
            raise HTTPException(status_code=400, detail="This role cannot be assigned to approval steps")

        # disallow duplicate positions
        for n in route.nodes:
            if n.id != node.id and n.approver and n.approver.profile and n.approver.profile.role:
                existing_role = n.approver.profile.role
                if existing_role.level == profile.role.level and existing_role.sort_order == profile.role.sort_order:
                    raise HTTPException(status_code=409, detail="A role with this level and order already exists in the route")

        # validate role ordering relative to connected edges (incoming must be lower, outgoing must be higher)
        node_by_id = {n.id: n for n in route.nodes}
        for e in route.edges:
            # incoming edge: e.from_node -> node
            if e.to_node_id == node.id:
                prev_node = node_by_id.get(e.from_node_id)
                if not prev_node or not prev_node.approver or not prev_node.approver.profile or not prev_node.approver.profile.role:
                    raise HTTPException(status_code=400, detail="Invalid route nodes")
                prev_role = prev_node.approver.profile.role
                new_role = profile.role
                if new_role.level < prev_role.level or (new_role.level == prev_role.level and new_role.sort_order <= prev_role.sort_order):
                    raise HTTPException(status_code=400, detail="Approver order must go from lower to higher (by level then sort_order)")

            # outgoing edge: node -> e.to_node
            if e.from_node_id == node.id:
                next_node = node_by_id.get(e.to_node_id)
                if not next_node or not next_node.approver or not next_node.approver.profile or not next_node.approver.profile.role:
                    raise HTTPException(status_code=400, detail="Invalid route nodes")
                next_role = next_node.approver.profile.role
                new_role = profile.role
                if next_role.level < new_role.level or (next_role.level == new_role.level and next_role.sort_order <= new_role.sort_order):
                    raise HTTPException(status_code=400, detail="Approver order must go from lower to higher (by level then sort_order)")

        node.approver_id = payload.approver_id  # type: ignore

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
        # build a transient edge object and run validations before persisting
        new_edge = RouteEdge(route_id=route_id, from_node_id=from_node.id, to_node_id=to_node.id)

        nodes = route.nodes
        edges = route.edges + [new_edge]
        _validate_acyclic(nodes, edges)

        # validate sequential chain: indegree/outdegree must be <=1 and route must be a single linear chain
        incoming = defaultdict(int)
        outgoing = defaultdict(int)
        for e in edges:
            outgoing[e.from_node_id] += 1
            incoming[e.to_node_id] += 1

        # every node must have indegree<=1 and outdegree<=1
        for n in nodes:
            if incoming[n.id] > 1 or outgoing[n.id] > 1:
                raise HTTPException(status_code=400, detail="Route must be strictly sequential (no branching allowed)")

        # require at least 2 nodes
        if len(nodes) < 2:
            raise HTTPException(status_code=400, detail="Route must contain at least 2 steps")

        # check role ordering for each edge
        node_by_id = {n.id: n for n in nodes}
        for e in edges:
            a = node_by_id.get(e.from_node_id)
            b = node_by_id.get(e.to_node_id)
            if not a or not b or not a.approver or not b.approver:
                raise HTTPException(status_code=400, detail="Invalid route nodes")
            role_a = a.approver.profile.role if a.approver.profile else None
            role_b = b.approver.profile.role if b.approver.profile else None
            if not role_a or not role_b:
                raise HTTPException(status_code=400, detail="Approver roles must have level and order defined")

            if role_b.level < role_a.level or (role_b.level == role_a.level and role_b.sort_order <= role_a.sort_order):
                raise HTTPException(status_code=400, detail="Approver order must go from lower to higher (by level then sort_order)")

        # persist the edge after all checks passed
        edge = await RouteRepository.create_edge(new_edge, db)
        await db.commit()
        await db.refresh(edge)
        return edge
    except HTTPException:
        # nothing persisted here except possible earlier DB state; ensure rollback for safety
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
            approver_full_name= node.approver.profile.second_name + ' ' + node.approver.profile.first_name + ' ' + node.approver.profile.third_name if node.approver else None,
            step_index=node.step_index,
            incoming_count=incoming[node.id],
            outgoing_count=outgoing[node.id],
            is_start=incoming[node.id] == 0,
            is_terminal=outgoing[node.id] == 0,
            level=level_by_node.get(node.id, 0),
            approver_role_name=(node.approver.profile.role.name if node.approver and node.approver.profile and node.approver.profile.role else None),
            approver_unit_name=(node.approver.profile.unit.name if node.approver and node.approver.profile and node.approver.profile.unit else None),
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