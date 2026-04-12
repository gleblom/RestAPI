from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.database import get_session
from src.exceptions import AlreadyExists
from src.models.users import Profile
from src.schemas.users import ProfileDTO, UserUpdateDTO
from src.security import CurrentUser, RoleChecker
from src.services.profile_service import add_profile_service, update_profile_service
from src.services.user_service import get_users_service, update_user_company_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

role_checker = RoleChecker([1, 2]) #id базовых ролей: 1 - Директор, 2 - Админ 3 - Делопроизводитель

@router.put("/company")
async def update_user_company(db: Annotated[AsyncSession, Depends(get_session)], company: UserUpdateDTO):
    try:
        user = await update_user_company_service(db, cast(UUID, company.company_id), cast(UUID, company.director_id))
        return user
    except:
        return JSONResponse(
            content={"message": "Database Error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

@router.get("/all", status_code=status.HTTP_200_OK)
async def get_users(db: Annotated[AsyncSession, Depends(get_session)], current_user: CurrentUser):
    users = await get_users_service(db, cast(UUID, current_user.company_id))
    return users

#Создание профиля администратором или директором 
@router.post("/profile", response_model=ProfileDTO, status_code=status.HTTP_201_CREATED, dependencies=[Depends(role_checker)])
async def create_profile(
    db: Annotated[AsyncSession, Depends(get_session)], 
    current_user: CurrentUser, 
    profile: ProfileDTO,
    ):
    try:   
        if current_user.company_id == profile.company_id:
            created_profile = await add_profile_service(db, profile)
            
            new_profile = ProfileDTO(
                id = created_profile.id,
                first_name=created_profile.first_name,
                second_name=created_profile.second_name,
                third_name=created_profile.third_name,
                company_id=cast(UUID, created_profile.company_id),
                role_id=created_profile.role_id,
                unit_id=created_profile.unit_id
            )
            
            return new_profile
   
    except AlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Database error")
        

@router.put("/profile", dependencies=[Depends(role_checker)])
async def update_profile(db: Annotated[AsyncSession, Depends(get_session)], current_user: CurrentUser, profile: ProfileDTO):
    
    if current_user.company_id == profile.company_id:
        updated_profile = await update_profile_service(db, profile)

        return updated_profile
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not allowed to perfrom this action"
    )