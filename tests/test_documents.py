import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi import HTTPException

import src.services.document_service as doc_svc


@pytest.mark.asyncio
async def test_create_document_service_success(monkeypatch):
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, unit_id=10, company_id=uuid4())
    payload = SimpleNamespace(title='Doc', unit_id=10, expires_at=None, category_id=1)
    created_doc = SimpleNamespace(id=uuid4(), title='Doc', author_id=user_id, status_id=2, current_step_index=0)

    monkeypatch.setattr(doc_svc.DocumentRepository, 'create_document', AsyncMock(return_value=created_doc))
    monkeypatch.setattr(doc_svc.DocumentRepository, 'create_document_unit', AsyncMock(return_value=SimpleNamespace()))
    db = SimpleNamespace(flush=AsyncMock(), commit=AsyncMock(), refresh=AsyncMock())

    res = await doc_svc.create_document_service(db, current_user, payload)
    assert res.id == created_doc.id


@pytest.mark.asyncio
async def test_create_document_service_forbidden_unit():
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, unit_id=10, company_id=uuid4())
    payload = SimpleNamespace(title='Doc', unit_id=11, expires_at=None, category_id=1)
    db = SimpleNamespace()
    with pytest.raises(HTTPException) as ex:
        await doc_svc.create_document_service(db, current_user, payload)
    assert ex.value.status_code == 403


@pytest.mark.asyncio
async def test_create_document_version_document_not_found(monkeypatch):
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, unit_id=1, company_id=uuid4())
    monkeypatch.setattr(doc_svc.DocumentRepository, 'get_document_by_id', AsyncMock(return_value=None))
    db = SimpleNamespace()
    with pytest.raises(HTTPException) as ex:
        await doc_svc.create_document_version_service(db, current_user, uuid4(), SimpleNamespace(version_number=None, storage_object_name='x', original_file_name='a.pdf', mime_type='application/pdf', file_size=123))
    assert ex.value.status_code == 404


@pytest.mark.asyncio
async def test_create_document_version_not_author(monkeypatch):
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, unit_id=1, company_id=uuid4())
    doc = SimpleNamespace(id=uuid4(), author_id=uuid4())
    monkeypatch.setattr(doc_svc.DocumentRepository, 'get_document_by_id', AsyncMock(return_value=doc))
    db = SimpleNamespace()
    with pytest.raises(HTTPException) as ex:
        await doc_svc.create_document_version_service(db, current_user, doc.id, SimpleNamespace(version_number=None, storage_object_name='x', original_file_name='a.pdf', mime_type='application/pdf', file_size=123))
    assert ex.value.status_code == 403


@pytest.mark.asyncio
async def test_get_document_service_access_denied(monkeypatch):
    user_id = uuid4()
    current_user = SimpleNamespace(user_id=user_id, unit_id=99, company_id=uuid4())
    doc = SimpleNamespace(id=uuid4(), author_id=uuid4(), status_id=2)
    monkeypatch.setattr(doc_svc.DocumentRepository, 'get_document_by_id', AsyncMock(return_value=doc))

    class DummyRes:
        def scalars(self):
            return self

        def all(self):
            return []

    db = SimpleNamespace(execute=AsyncMock(return_value=DummyRes()))

    with pytest.raises(HTTPException) as ex:
        await doc_svc.get_document_service(db, current_user, doc.id)
    assert ex.value.status_code == 403
