
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import Profile
from models.views import VUser


class ProfileRepository:        
    @staticmethod
    async def create_profile(profile: Profile, db: AsyncSession) -> Profile:
        db.add(Profile)
        
        await db.flush()
        
        return profile
    
    @staticmethod
    async def get_profile_by_id(user_id: UUID, db: AsyncSession) -> VUser | None:
        result = await db.execute(select(VUser).where(VUser.user_id == user_id))
        return result.scalar_one_or_none()

    
    @staticmethod
    async def get_users_by_company(company_id: UUID, db:AsyncSession):
        result = await db.execute(select(VUser).where(VUser.company_id == company_id))
        
        return result.all()
    
    @staticmethod
    async def update_profile(profile_data: dict, profile: Profile, db: AsyncSession):
        
        for k, v in profile_data.items():
            setattr(profile, k, v)
            
        await db.flush()
        
        return profile