import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi import HTTPException

import src.services.route_service as rs


def test_toposort_levels_simple():
    nodes = [SimpleNamespace(id=1, step_index=0), SimpleNamespace(id=2, step_index=1)]
    edges = [SimpleNamespace(from_node_id=1, to_node_id=2)]
    levels = rs._toposort_levels(nodes, edges)
    assert levels == [[1], [2]]


def test_validate_acyclic_cycle_raises():
    nodes = [SimpleNamespace(id=1, step_index=0), SimpleNamespace(id=2, step_index=1)]
    edges = [SimpleNamespace(from_node_id=1, to_node_id=2), SimpleNamespace(from_node_id=2, to_node_id=1)]
    with pytest.raises(Exception):
        rs._validate_acyclic(nodes, edges)


@pytest.mark.asyncio
async def test_add_node_duplicate_step(monkeypatch):
    route = SimpleNamespace(nodes=[SimpleNamespace(step_index=1)], id=1, company_id=uuid4())
    monkeypatch.setattr(rs.RouteRepository, 'get_route', AsyncMock(return_value=route))
    current_user = SimpleNamespace(company_id=route.company_id)
    payload = SimpleNamespace(step_index=1, approver_id=uuid4())
    db = SimpleNamespace()
    with pytest.raises(HTTPException) as ex:
        await rs.add_node_service(db, current_user, 1, payload)
    assert ex.value.status_code == 409


@pytest.mark.asyncio
async def test_add_edge_self_loop(monkeypatch):
    route = SimpleNamespace(nodes=[SimpleNamespace(id=1)], edges=[], id=1, company_id=uuid4())
    monkeypatch.setattr(rs.RouteRepository, 'get_route', AsyncMock(return_value=route))
    monkeypatch.setattr(rs.RouteRepository, 'get_node', AsyncMock(side_effect=[SimpleNamespace(id=1, route_id=1), SimpleNamespace(id=1, route_id=1)]))
    monkeypatch.setattr(rs.RouteRepository, 'edge_exists', AsyncMock(return_value=False))
    current_user = SimpleNamespace(company_id=route.company_id)
    payload = SimpleNamespace(from_node_id=1, to_node_id=1)
    db = SimpleNamespace()
    with pytest.raises(HTTPException) as ex:
        await rs.add_edge_service(db, current_user, 1, payload)
    assert ex.value.status_code == 400

@pytest.mark.asyncio
async def test_get_route_graph_service_cycle_detected(monkeypatch):
    route = SimpleNamespace(
        nodes=[SimpleNamespace(id=1, step_index=0), SimpleNamespace(id=2, step_index=1)],
        edges=[SimpleNamespace(from_node_id=1, to_node_id=2), SimpleNamespace(from_node_id=2, to_node_id=1)],
        id=1,
        company_id=uuid4(),
    )
    monkeypatch.setattr(rs.RouteRepository, 'get_route', AsyncMock(return_value=route))
    current_user = SimpleNamespace(company_id=route.company_id)
    db = SimpleNamespace()
    with pytest.raises(Exception):
        await rs.get_route_graph_service(db, current_user, 1)
