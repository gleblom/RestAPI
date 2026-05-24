import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi import HTTPException

import src.services.approval_service as ap


def test_route_start_step_empty_nodes():
    with pytest.raises(HTTPException) as ex:
        ap._route_start_step([])
    assert ex.value.status_code == 400


@pytest.mark.asyncio
async def test_submit_document_route_not_found(monkeypatch):
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, company_id=uuid4())
    doc = SimpleNamespace(id=uuid4(), author_id=user_id, title='T')
    monkeypatch.setattr(ap.DocumentRepository, 'get_document_by_id', AsyncMock(return_value=doc))
    monkeypatch.setattr(ap.RouteRepository, 'get_route', AsyncMock(return_value=None))
    db = SimpleNamespace()
    with pytest.raises(HTTPException) as ex:
        await ap.submit_document_service(db, current_user, doc.id, SimpleNamespace(route_id=1))
    assert ex.value.status_code == 404


@pytest.mark.asyncio
async def test_submit_document_no_latest_version(monkeypatch):
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, company_id=uuid4())
    doc = SimpleNamespace(id=uuid4(), author_id=user_id, title='T')
    route = SimpleNamespace(id=1, nodes=[SimpleNamespace(step_index=1, id=10, approver_id=user_id)], company_id=current_user.company_id)
    monkeypatch.setattr(ap.DocumentRepository, 'get_document_by_id', AsyncMock(return_value=doc))
    monkeypatch.setattr(ap.RouteRepository, 'get_route', AsyncMock(return_value=route))
    monkeypatch.setattr(ap.DocumentRepository, 'get_latest_document_version', AsyncMock(return_value=None))
    db = SimpleNamespace()
    with pytest.raises(HTTPException) as ex:
        await ap.submit_document_service(db, current_user, doc.id, SimpleNamespace(route_id=1))
    assert ex.value.status_code == 400


@pytest.mark.asyncio
async def test_reject_document_empty_comment(monkeypatch):
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, company_id=uuid4())
    with pytest.raises(HTTPException) as ex:
        await ap.reject_document_service(None, current_user, uuid4(), "   ")
    assert ex.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_document_not_approver(monkeypatch):
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, company_id=uuid4())
    doc = SimpleNamespace(id=uuid4(), route_id=1, author_id=uuid4(), current_step_index=1, status_id=3)
    latest = SimpleNamespace(id=1)
    current_node = SimpleNamespace(step_index=1, id=10, approver_id=uuid4())
    monkeypatch.setattr(ap.DocumentRepository, 'get_document_by_id', AsyncMock(return_value=doc))
    monkeypatch.setattr(ap.DocumentRepository, 'get_latest_document_version', AsyncMock(return_value=latest))
    monkeypatch.setattr(ap.RouteRepository, 'get_route_node', AsyncMock(return_value=current_node))
    db = SimpleNamespace()

    with pytest.raises(HTTPException) as ex:
        await ap.approve_document_service(db, current_user, doc.id)
    assert ex.value.status_code == 403
