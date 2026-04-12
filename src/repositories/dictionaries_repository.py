from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.dictionaries import Role, Unit, UnitCompany
from src.models.users import Profile


class DictionariesRepository:
    # ---- roles ----

    @staticmethod
    async def list_roles(company_id: UUID, db: AsyncSession):
        result = await db.execute(
            select(Role)
            .where((Role.company_id == company_id) | (Role.company_id.is_(None)))
            .order_by(func.lower(Role.name).asc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_role(role_id: int, db: AsyncSession) -> Role | None:
        result = await db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_role(role: Role, db: AsyncSession) -> Role:
        db.add(role)
        await db.flush()
        return role

    @staticmethod
    async def delete_role(role: Role, db: AsyncSession) -> None:
        await db.delete(role)

    @staticmethod
    async def role_name_exists(company_id: UUID, name: str, db: AsyncSession) -> bool:
        result = await db.execute(
            select(Role.id).where(
                func.lower(Role.name) == func.lower(name),
                Role.company_id == company_id,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def role_is_used(role_id: int, db: AsyncSession) -> bool:
        result = await db.execute(select(Profile.id).where(Profile.role_id == role_id))
        return result.scalar_one_or_none() is not None

    # ---- units ----

    @staticmethod
    async def get_unit(unit_id: int, db: AsyncSession) -> Unit | None:
        result = await db.execute(
            select(Unit)
            .where(Unit.id == unit_id)
            .options(selectinload(Unit.unit_companies))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_units(company_id: UUID, db: AsyncSession):
        result = await db.execute(
            select(Unit)
            .join(UnitCompany, UnitCompany.unit_id == Unit.id)
            .where(UnitCompany.company_id == company_id)
            .options(selectinload(Unit.unit_companies))
            .order_by(func.lower(Unit.name).asc())
        )
        return result.scalars().unique().all()

    @staticmethod
    async def create_unit(unit: Unit, db: AsyncSession) -> Unit:
        db.add(unit)
        await db.flush()
        return unit

    @staticmethod
    async def delete_unit(unit: Unit, db: AsyncSession) -> None:
        await db.delete(unit)

    @staticmethod
    async def unit_name_exists(name: str, db: AsyncSession) -> bool:
        result = await db.execute(
            select(Unit.id).where(func.lower(Unit.name) == func.lower(name))
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def replace_unit_companies(unit_id: int, company_ids: list[UUID], db: AsyncSession) -> None:
        await db.execute(delete(UnitCompany).where(UnitCompany.unit_id == unit_id))
        for company_id in company_ids:
            db.add(UnitCompany(unit_id=unit_id, company_id=company_id))
        await db.flush()

    @staticmethod
    async def add_unit_company(unit_id: int, company_id: UUID, db: AsyncSession) -> UnitCompany:
        link = UnitCompany(unit_id=unit_id, company_id=company_id)
        db.add(link)
        await db.flush()
        return link

    @staticmethod
    async def remove_unit_company(unit_id: int, company_id: UUID, db: AsyncSession) -> None:
        await db.execute(
            delete(UnitCompany).where(
                UnitCompany.unit_id == unit_id,
                UnitCompany.company_id == company_id,
            )
        )

    @staticmethod
    async def unit_company_ids(unit_id: int, db: AsyncSession) -> list[UUID]:
        result = await db.execute(
            select(UnitCompany.company_id).where(UnitCompany.unit_id == unit_id)
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def unit_is_used(unit_id: int, db: AsyncSession) -> bool:
        result = await db.execute(select(Profile.id).where(Profile.unit_id == unit_id))
        return result.scalar_one_or_none() is not None