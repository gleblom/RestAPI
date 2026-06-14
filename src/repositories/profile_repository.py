
from typing import cast
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.schemas.users import ProfileDTO
from src.models.users import Profile
from src.models.views import VUser


class ProfileRepository:        
    @staticmethod
    async def create_profile(profile: ProfileDTO, db: AsyncSession) -> ProfileDTO:
        db.add(Profile)
        
        await db.flush()
        
        return profile
    
    @staticmethod
    async def get_profile_by_id(user_id: UUID, db: AsyncSession) -> VUser | None:
        result = await db.execute(select(VUser).where(VUser.user_id == user_id))
        return result.scalar_one_or_none()
    @staticmethod
    async def get_profile(user_id: UUID, db: AsyncSession) -> Profile | None:
        result = await db.execute(select(Profile).options(selectinload(Profile.role)).where(Profile.id == user_id))
        return result.scalar_one_or_none()

    
    @staticmethod
    async def get_users_by_company(
        company_id: UUID, 
        db:AsyncSession,
        user_name: str  | None = None,
        units: list[int]  | None = None,
        roles: list[int]  | None = None
        ):
        query = select(VUser)
        
        conditions = []

        conditions.append(VUser.company_id == company_id)
        
        if user_name:
            conditions.append(func.concat(VUser.first_name, '', VUser.second_name, '', VUser.third_name).like(f"%user_name%"))
        if units:
            conditions.append(VUser.unit_id.in_(units))
        if roles:
            conditions.append(VUser.role_id.in_(roles))
        if conditions:
            query = query.where(and_(*conditions))
            
        result = await db.execute(query)    

        return result.scalars().all()
    
    @staticmethod
    async def update_profile(profile_data: dict, profile_dto: ProfileDTO, db: AsyncSession):
        
        profile = await ProfileRepository.get_profile(cast(UUID, profile_dto.id), db)
        
        for k, v in profile_data.items():
            setattr(profile, k, v)
            
        await db.flush()
        
        return profile