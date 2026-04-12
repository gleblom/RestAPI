from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.users import ProfileDTO
from src.database import get_session
from src.exceptions import AlreadyExists
from src.models.users import Profile
from src.repositories.profile_repository import ProfileRepository

async def add_profile_service(db: Annotated[AsyncSession, Depends(get_session)], profile: ProfileDTO):
    user_profile = await ProfileRepository.get_profile_by_id(cast(UUID, profile.id), db)
    
    if user_profile:
        raise AlreadyExists("Profile already created")
    
    try:
        profile = await ProfileRepository.create_profile(profile, db)
        await db.commit()
        await db.refresh(profile)
        return profile
    except Exception as e:
        await db.rollback()
        raise e
    
async def update_profile_service(db: Annotated[AsyncSession, Depends(get_session)], profile:ProfileDTO):
    try:
        
        updated_profile = await ProfileRepository.update_profile(
            {
             "first_name": profile.first_name,
             "second_name": profile.second_name,
             "third_name": profile.third_name,
             "role_id": profile.role_id,
             "unit_id": profile.unit_id
             }, 
            profile, db)
        
        await db.commit()
        
        return updated_profile
    except Exception as e:
        await db.rollback()
        raise e