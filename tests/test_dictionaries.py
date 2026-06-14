import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from fastapi import HTTPException
from uuid import uuid4

import src.services.dictionaries_service as ds


@pytest.mark.asyncio
async def test_create_role_success(monkeypatch):
    company_id = uuid4()
    payload = SimpleNamespace(name="NewRole", level=1)
    current_user = SimpleNamespace(company_id=company_id)
    mock_role = SimpleNamespace(id=1, name="NewRole", company_id=company_id)

    monkeypatch.setattr(ds.DictionariesRepository, "role_name_exists", AsyncMock(return_value=False))
    monkeypatch.setattr(ds.DictionariesRepository, "create_role", AsyncMock(return_value=mock_role))
    monkeypatch.setattr(ds.DictionariesRepository, "next_sort_order", AsyncMock(return_value=1))
    monkeypatch.setattr(ds.DictionariesRepository, "role_with_level_exists", AsyncMock(return_value=False))

    db = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())

    res = await ds.create_role_service(db, current_user, payload)
    assert res.name == "NewRole"


@pytest.mark.asyncio
async def test_create_role_empty_name():
    payload = SimpleNamespace(name="   ", level=1)
    current_user = SimpleNamespace(company_id=uuid4())
    db = SimpleNamespace()

    with pytest.raises(HTTPException) as ex:
        await ds.create_role_service(db, current_user, payload)
    assert ex.value.status_code == 400


@pytest.mark.asyncio
async def test_create_role_duplicate_name(monkeypatch):
    payload = SimpleNamespace(name="Dup", level=1)
    current_user = SimpleNamespace(company_id=uuid4())
    monkeypatch.setattr(ds.DictionariesRepository, "role_name_exists", AsyncMock(return_value=True))
    db = SimpleNamespace()

    with pytest.raises(HTTPException) as ex:
        await ds.create_role_service(db, current_user, payload)
    assert ex.value.status_code == 409


@pytest.mark.asyncio
async def test_delete_role_not_found(monkeypatch):
    current_user = SimpleNamespace(company_id=uuid4())
    monkeypatch.setattr(ds.DictionariesRepository, "get_role", AsyncMock(return_value=None))
    db = SimpleNamespace()

    with pytest.raises(HTTPException) as ex:
        await ds.delete_role_service(db, current_user, 123)
    assert ex.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_role_in_use(monkeypatch):
    role = SimpleNamespace(id=5, company_id=uuid4())
    current_user = SimpleNamespace(company_id=role.company_id)
    monkeypatch.setattr(ds.DictionariesRepository, "get_role", AsyncMock(return_value=role))
    monkeypatch.setattr(ds.DictionariesRepository, "role_is_used", AsyncMock(return_value=True))
    db = SimpleNamespace()

    with pytest.raises(HTTPException) as ex:
        await ds.delete_role_service(db, current_user, 5)
    assert ex.value.status_code == 409
