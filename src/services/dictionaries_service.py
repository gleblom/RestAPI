from __future__ import annotations

from select import select
from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import AlreadyExists
from src.repositories.company_repository import CompanyRepository
from src.models.dictionaries import Role, RoleCategory, Unit
from src.repositories.dictionaries_repository import DictionariesRepository
from src.schemas.dictionaries import (
    RoleCategoryDTO,
    RoleCreateDTO,
    RoleReadDTO,
    RoleUpdateDTO,
    UnitCreateDTO,
    UnitReadDTO,
    UnitUpdateDTO,
)
from src.security import CurrentUser


async def list_roles_service(db: AsyncSession, current_user: CurrentUser):
    return await DictionariesRepository.list_roles(cast(UUID, current_user.company_id), db)


async def create_role_service(db: AsyncSession, current_user: CurrentUser, payload: RoleCreateDTO) -> RoleReadDTO:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role name is required")

    if await DictionariesRepository.role_name_exists(cast(UUID, current_user.company_id), name, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")

    try:
        role = await DictionariesRepository.create_role(
            Role(name=name, company_id=current_user.company_id),
            db,
        )
        await db.commit()
        await db.refresh(role)
        return RoleReadDTO.model_validate(role)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while creating role") from e


async def update_role_service(db: AsyncSession, current_user: CurrentUser, role_id: int, payload: RoleUpdateDTO) -> RoleReadDTO:
    role = await DictionariesRepository.get_role(role_id, db)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.company_id not in (None, current_user.company_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role name is required")
        if await DictionariesRepository.role_name_exists(cast(UUID, current_user.company_id), name, db):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
        role.name = name

    try:
        await db.commit()
        await db.refresh(role)
        return RoleReadDTO.model_validate(role)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while updating role") from e


async def delete_role_service(db: AsyncSession, current_user: CurrentUser, role_id: int):
    role = await DictionariesRepository.get_role(role_id, db)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.company_id not in (None, current_user.company_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if await DictionariesRepository.role_is_used(role_id, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role is already assigned to users")

    try:
        await DictionariesRepository.delete_role(role, db)
        await db.commit()
        return {"detail": "Role deleted"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while deleting role") from e


async def list_units_service(db: AsyncSession, current_user: CurrentUser):
    units = await DictionariesRepository.list_units(cast(UUID, current_user.company_id), db)
    result = []
    for unit in units:
        company_ids = await DictionariesRepository.unit_company_ids(unit.id, db)
        result.append(UnitReadDTO(id=unit.id, name=unit.name, company_ids=company_ids))
    return result


async def create_unit_service(db: AsyncSession, current_user: CurrentUser, payload: UnitCreateDTO) -> UnitReadDTO:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit name is required")

    try:
        unit = await DictionariesRepository.create_unit(Unit(name=name), db)
        company_ids = payload.company_ids or [current_user.company_id]
        await DictionariesRepository.replace_unit_companies(unit.id, company_ids, db) # type: ignore
        await db.commit()
        await db.refresh(unit)
        return UnitReadDTO(id=unit.id, name=unit.name, company_ids=company_ids) # type: ignore
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while creating unit") from e


async def update_unit_service(db: AsyncSession, current_user: CurrentUser, unit_id: int, payload: UnitUpdateDTO) -> UnitReadDTO:
    unit = await DictionariesRepository.get_unit(unit_id, db)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit name is required")
        unit.name = name

    if payload.company_ids is not None:
        await DictionariesRepository.replace_unit_companies(unit.id, payload.company_ids, db)

    try:
        await db.commit()
        await db.refresh(unit)
        company_ids = await DictionariesRepository.unit_company_ids(unit.id, db)
        return UnitReadDTO(id=unit.id, name=unit.name, company_ids=company_ids)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while updating unit") from e


async def delete_unit_service(db: AsyncSession, current_user: CurrentUser, unit_id: int):
    unit = await DictionariesRepository.get_unit(unit_id, db)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if await DictionariesRepository.unit_is_used(unit_id, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unit is already assigned to users")

    try:
        await DictionariesRepository.remove_unit_company(unit.id, cast(UUID, current_user.company_id), db)
        remaining = await DictionariesRepository.unit_company_ids(unit.id, db)
        if not remaining:
            await DictionariesRepository.delete_unit(unit, db)
        await db.commit()
        return {"detail": "Unit deleted"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while deleting unit") from e


async def attach_unit_to_company_service(db: AsyncSession, current_user: CurrentUser, unit_id: int, company_id: UUID):
    unit = await DictionariesRepository.get_unit(unit_id, db)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if current_user.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to attach unit to this company")

    try:
        await DictionariesRepository.add_unit_company(unit.id, company_id, db)
        await db.commit()
        company_ids = await DictionariesRepository.unit_company_ids(unit.id, db)
        return UnitReadDTO(id=unit.id, name=unit.name, company_ids=company_ids)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company link already exists")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while linking unit to company") from e


async def detach_unit_from_company_service(db: AsyncSession, current_user: CurrentUser, unit_id: int, company_id: UUID):
    unit = await DictionariesRepository.get_unit(unit_id, db)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    company_unit = await CompanyRepository.get_company_units(cast(UUID, current_user.company_id), unit_id, db)
    if not company_unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    try:
        await DictionariesRepository.remove_unit_company(unit.id, company_id, db)
        remaining = await DictionariesRepository.unit_company_ids(unit.id, db)
        if not remaining and not await DictionariesRepository.unit_is_used(unit.id, db):
            await DictionariesRepository.delete_unit(unit, db)
        await db.commit()
        return {"detail": "Company detached from unit"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while unlinking unit from company") from e

async def get_role_categories_service(db: AsyncSession, role_id: int, current_user: CurrentUser):
    role = await DictionariesRepository.get_role(role_id, db)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    try:
        role_categories = await DictionariesRepository.get_role_categories(role_id, db)
        return role_categories
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error while getting role categories") from e
    
    
async def add_role_categories_service(db: AsyncSession, payload: RoleCategoryDTO, current_user: CurrentUser):
    try:
        role = await DictionariesRepository.get_role(payload.role_id, db)
        
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
        if role.id == 1 or role.id == 2 or role.id == 3:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You can't add categories to this roles")
        
        if role.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to add role categories to this company")
            
        
        role_categories = await DictionariesRepository.get_role_categories(payload.role_id, db)
        
        if role_categories:
            raise AlreadyExists("Role categories Already Exists")
        
        await DictionariesRepository.add_role_categories(payload.category_ids, payload.role_id, db)
        
        await db.commit()
        
        new_role_categories = await DictionariesRepository.get_role_categories(payload.role_id, db)        
        return new_role_categories
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from e
    
async def update_role_categories_service(db: AsyncSession, payload: RoleCategoryDTO, current_user: CurrentUser):
    try:
        role = await DictionariesRepository.get_role(payload.role_id, db)
        
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
        if role.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to update role categories to this company")
        
        role_categories = list(await DictionariesRepository.get_role_categories(payload.role_id, db))
        
        current_categories = set([x.category_id for x in role_categories])
        
        categories_to_add = [x for x in payload.category_ids if x not in current_categories]
        categories_to_remove = [x for x in current_categories if x not in payload.category_ids]
        

        new_role_categories = list(
            filter(
                lambda category_id: 
                    RoleCategory(
                        role_id = payload.role_id, 
                        category_id = category_id), 
                    categories_to_add))
        if any(new_role_categories):
            await DictionariesRepository.add_role_categories(new_role_categories, payload.role_id, db)
        if any(categories_to_remove):
            records_to_delete = list(
                filter(
                    lambda rc: 
                        rc.category_id in categories_to_remove, 
                        role_categories))
            await DictionariesRepository.delete_role_categories(records_to_delete, db)
        
        await db.commit()
        
        updated_role_categories = await DictionariesRepository.get_role_categories(payload.role_id, db)
        
        return updated_role_categories
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from e
            
async def get_categories_service(db: AsyncSession):
    try:
        return await DictionariesRepository.get_categories(db)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from e
    
        
async def get_statuses_service(db):
    try:
        return await DictionariesRepository.get_statuses(db)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error") from e   
        
    
            