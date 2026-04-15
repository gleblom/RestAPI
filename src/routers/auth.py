from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.database import get_session
from src.exceptions import AlreadyExists, Authentication
from src.repositories.user_repository import UserRepository
from src.schemas.users import UserPublicDTO, UserTokenDTO
from src.security import CurrentUser

from src.services.user_service import (
    add_user_service, 
    delete_token_service, 
    login_user_service, 
    logout_user_service, 
    refresh_access_token_service,
    reset_password_service, 
    send_email_confirmation_service,
    send_recovery_token_service
    )
from src.config import Config

from src.schemas import UserCreateDTO, UserReadDTO

import resend

settings = Config() # type: ignore

resend.api_key = settings.api_key.get_secret_value()

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    "/register", 
    response_model=UserReadDTO, 
    status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreateDTO, background_task: BackgroundTasks, db: Annotated[AsyncSession, Depends(get_session)]):
    try:
        created_user = await add_user_service(
            db = db, 
            email = user.email, 
            password = user.password
            )
    
        
        background_task.add_task(send_email_confirmation_service, user.email, db)
        
        return created_user
    
    except AlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Database error")

@router.get("/confirm-email", status_code=status.HTTP_200_OK)
async def verify_user_account(token: str, db: Annotated[AsyncSession, Depends(get_session)]):
    user = await delete_token_service(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired token")

    await UserRepository.update_user({"is_email_verified": True}, user, db)
    await db.commit()
    return {"message": "Account verified successfully"}
    
@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    
    background_tasks.add_task(send_recovery_token_service, email, db)

    return {
        "message": "If an account exists with this email, you will receive password reset instructions.",
    }

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    token: str,
    password: str,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    await reset_password_service(token, password, db)
    
    return {
        "message": "Password reset successfully. You can now log in with your new password.",
    }
    

@router.post("/login", response_model=UserTokenDTO)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_session)]
):
    try:
        access_token, refresh_token_value = await login_user_service(db, form_data.username, form_data.password)
    except Authentication as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    
    return UserTokenDTO(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token_value
    )


@router.post("/refresh", response_model=UserTokenDTO)
async def refresh_access_token(
    db: Annotated[AsyncSession, Depends(get_session)],
    refresh_token_value: str = Body(..., embed=True)
):
    try:
        access_token, new_refresh_token_value = await refresh_access_token_service(db, refresh_token_value)
    except Authentication as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    
    return UserTokenDTO(
        access_token=access_token,
        token_type="bearer",
        refresh_token=new_refresh_token_value
    )
    
@router.post("/logout")
async def logout(
    db: Annotated[AsyncSession, Depends(get_session)],
    refresh_token_value: str = Body(..., embed=True)
):
    await logout_user_service(
        db=db,
        refresh_token_value=refresh_token_value,
    )
    
    return {"detail": "Successfully logged out"}

@router.get("/me", response_model=UserReadDTO)
async def get_current_user(current_user: CurrentUser): 
    return UserReadDTO(
        id = cast(UUID, current_user.user_id),
        email=current_user.user_email,
        phone=current_user.user_phone,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        created_at=current_user.user_created_at
    )

@router.get("/{user_id}", response_model=UserPublicDTO)
async def get_user_by_id(user_id: UUID, db: Annotated[AsyncSession, Depends(get_session)]):
    user = await UserRepository.get_user_by_id(user_id, db)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserPublicDTO(id=cast(UUID, user.id))


