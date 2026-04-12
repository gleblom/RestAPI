from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.dictionaries import (
    RoleCreateDTO,
    RoleReadDTO,
    RoleUpdateDTO,
    UnitCreateDTO,
    UnitReadDTO,
    UnitUpdateDTO,
)
from src.security import CurrentUser, RoleChecker
from src.services.dictionaries_service import (
    attach_unit_to_company_service,
    create_role_service,
    create_unit_service,
    delete_role_service,
    delete_unit_service,
    detach_unit_from_company_service,
    list_roles_service,
    list_units_service,
    update_role_service,
    update_unit_service,
)

router = APIRouter(prefix="/dictionaries", tags=["dictionaries"])
role_checker = RoleChecker([1, 2])  # 1 - Директор, 2 - Админ


@router.get("/roles", response_model=list[RoleReadDTO], dependencies=[Depends(role_checker)])
async def get_roles(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await list_roles_service(db, current_user)


@router.post("/roles", response_model=RoleReadDTO, status_code=status.HTTP_201_CREATED, dependencies=[Depends(role_checker)])
async def create_role(
    payload: RoleCreateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await create_role_service(db, current_user, payload)


@router.put("/roles/{role_id}", response_model=RoleReadDTO, dependencies=[Depends(role_checker)])
async def update_role(
    role_id: int,
    payload: RoleUpdateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await update_role_service(db, current_user, role_id, payload)


@router.delete("/roles/{role_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(role_checker)])
async def delete_role(
    role_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await delete_role_service(db, current_user, role_id)


@router.get("/units", response_model=list[UnitReadDTO], dependencies=[Depends(role_checker)])
async def get_units(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await list_units_service(db, current_user)


@router.post("/units", response_model=UnitReadDTO, status_code=status.HTTP_201_CREATED, dependencies=[Depends(role_checker)])
async def create_unit(
    payload: UnitCreateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await create_unit_service(db, current_user, payload)


@router.put("/units/{unit_id}", response_model=UnitReadDTO, dependencies=[Depends(role_checker)])
async def update_unit(
    unit_id: int,
    payload: UnitUpdateDTO,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await update_unit_service(db, current_user, unit_id, payload)


@router.delete("/units/{unit_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(role_checker)])
async def delete_unit(
    unit_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await delete_unit_service(db, current_user, unit_id)


@router.post("/units/{unit_id}/companies/{company_id}", response_model=UnitReadDTO, dependencies=[Depends(role_checker)])
async def attach_unit_to_company(
    unit_id: int,
    company_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await attach_unit_to_company_service(db, current_user, unit_id, company_id)


@router.delete("/units/{unit_id}/companies/{company_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(role_checker)])
async def detach_unit_from_company(
    unit_id: int,
    company_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
):
    return await detach_unit_from_company_service(db, current_user, unit_id, company_id)