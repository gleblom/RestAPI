import logging
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.database import get_session
from src.schemas.users import ProfileDTO, UserFullDTO, UserUpdateDTO
from src.security import CurrentUser, RoleChecker
from src.services.profile_service import update_profile_service
from src.services.user_service import get_users_service, update_user_company_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

role_checker = RoleChecker([1, 2]) #id базовых ролей: 1 - Директор, 2 - Админ 3 - Делопроизводитель

logger = logging.getLogger("uvicorn.access")

@router.put("/company")
async def update_user_company(db: Annotated[AsyncSession, Depends(get_session)], company: UserUpdateDTO):
    try:
        user = await update_user_company_service(db, cast(UUID, company.company_id), cast(UUID, company.director_id))
        if user:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except SQLAlchemyError as e:
        
        return JSONResponse(
            content={"message": e},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

@router.get("/all/", status_code=status.HTTP_200_OK, response_model=list[UserFullDTO]) 
async def get_users(
    db: Annotated[AsyncSession, Depends(get_session)], 
    current_user: CurrentUser,
    user_name: str | None = None,
    units: Annotated[list[int] | None, Query()] = None,
    roles: Annotated[list[int] | None, Query()] = None, 
    ):
    users = await get_users_service(db, cast(UUID, current_user.company_id), user_name, units, roles)
    return users

@router.put("/user/profile", response_model=ProfileDTO, status_code=status.HTTP_201_CREATED)
async def create_profile(
    db: Annotated[AsyncSession, Depends(get_session)], 
    current_user: CurrentUser, 
    profile: ProfileDTO,
    ):
    try:   
        if current_user.user_id == profile.id:
            updated_profile = await update_profile_service(db, profile)
            
            return updated_profile
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to perfrom this action")
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Database error")
        

@router.put("/profile", response_model=ProfileDTO, dependencies=[Depends(role_checker)])
async def update_profile(db: Annotated[AsyncSession, Depends(get_session)], current_user: CurrentUser, profile: ProfileDTO):
   
    if current_user.company_id == profile.company_id:
        updated_profile = await update_profile_service(db, profile)

        return updated_profile
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not allowed to perfrom this action"
    )