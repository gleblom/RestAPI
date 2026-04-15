
from datetime import UTC, datetime, timedelta
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.users import ProfileDTO
from src.database import get_session
from src.exceptions import AccountNotVerified, AlreadyExists, Authentication, InvalidToken, NotActiveUser, NotFound
from src.models.users import RefreshToken, User, UserToken
from src.repositories.profile_repository import ProfileRepository
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.user_repository import UserRepository
from src.repositories.user_token import UserTokenRepository
from src.schemas.email import EmailResponseDTO
from src.security import (
    create_access_token,
    create_token, 
    get_refresh_token_expire_time, 
    hash_password, hash_token, 
    verify_password,
    verify_token)

from src.config import Config

import resend

settings = Config() # type: ignore

resend.api_key = settings.api_key.get_secret_value()

async def add_user_service(db: Annotated[AsyncSession, Depends(get_session)], email: str, password: str) -> User:
    
    existing_user = await UserRepository.get_user_by_email(email, db)
    if existing_user:
        raise AlreadyExists("Email already registered")
    
    new_user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        is_active=True,
        is_email_verified=False,
    )
    
    try:
        created_user = await UserRepository.create_user(new_user, db)
        await db.commit()
        await db.refresh(created_user)
        return created_user
    except Exception as e:
        await db.rollback()
        raise e
 
async def update_user_company_service(db: Annotated[AsyncSession, Depends(get_session)], company_id: UUID, user_id: UUID):
    
    profile = await ProfileRepository.get_profile(user_id, db)
    
    if not profile:
        raise NotFound("User not found")
    
    try:
        dto = ProfileDTO(id=cast(UUID, profile.id), first_name=None, second_name=None, third_name=None, role_id=None, unit_id=None, company_id=None)
        await ProfileRepository.update_profile({"company_id": company_id}, dto, db)    
 
    except Exception as e:
        await db.rollback()
        raise e     

async def login_user_service(db: Annotated[AsyncSession, Depends(get_session)], email: str, password: str) -> tuple[str, str]:
    user = await UserRepository.get_user_by_email(email, db)
    if not user or not verify_password(password, user.password_hash): 
        raise Authentication("Invalid email or password")
    
    if not user.is_email_verified:
        raise AccountNotVerified("Account not yet verified")
    
    if not user.is_active:
        raise NotActiveUser("User is not active")
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    
    refresh_token_value, hashed_token_value = create_token()
    
    refresh_token = RefreshToken(
        token_hash=hashed_token_value,
        user_id=user.id,
        expires_at=get_refresh_token_expire_time(),
        is_revoked=False
    )
    
    await RefreshTokenRepository.create_refresh_token(refresh_token, db)
    
    await db.commit()
    
    return access_token, refresh_token_value

async def refresh_access_token_service(
    db: Annotated[AsyncSession, Depends(get_session)], 
    refresh_token_value: str, 
    ) -> tuple[str, str]:
    
    token_hash = hash_token(refresh_token_value)
    
    refresh_token = await RefreshTokenRepository.get_token(token_hash, db)
    
    if not refresh_token or refresh_token.is_revoked or not verify_token(refresh_token_value, refresh_token.token_hash): 
        raise Authentication("Invalid or expired refresh token")
    
    if await RefreshTokenRepository.is_expired(refresh_token):
        await RefreshTokenRepository.revoke_refresh_token(refresh_token, db)
        await db.commit()
        raise InvalidToken("Refresh token has expired")
    
    user = await UserRepository.get_user_by_id(cast(UUID, refresh_token.user_id), db)
    if not user:
        raise NotFound("User not found")
    
    await RefreshTokenRepository.revoke_refresh_token(refresh_token, db)
    
    new_refresh_token_value, hashed_new_refresh_token = create_token()
    new_refresh_token = RefreshToken(
        token_hash=hashed_new_refresh_token,
        user_id=user.id,
        expires_at=get_refresh_token_expire_time(),
        is_revoked=False
    )
    
    await RefreshTokenRepository.create_refresh_token(new_refresh_token, db)
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    
    await db.commit()
    
    return access_token, new_refresh_token_value

async def logout_user_service(db: Annotated[AsyncSession, Depends(get_session)], refresh_token_value: str) -> None:
    token_hash = hash_token(refresh_token_value)
    
    refresh_token = await RefreshTokenRepository.get_token(token_hash, db)
    
    if refresh_token and not refresh_token.is_revoked and verify_token(refresh_token_value, refresh_token.token_hash): 
        await RefreshTokenRepository.revoke_refresh_token(refresh_token, db)
        await db.commit()
      
async def get_users_service(db: Annotated[AsyncSession, Depends(get_session)], company_id: UUID):
   users = await ProfileRepository.get_users_by_company(company_id, db)
   
   return users
    
      
async def create_token_service(email: str, token_type: str, db: Annotated[AsyncSession, Depends(get_session)]) -> tuple[str, str]:
    
    token_value, token_hash = create_token()
    
    user = await UserRepository.get_user_by_email(email, db)
    
    if not user:
        raise NotFound("User Not Found")
        
    confirm_token = UserToken(
        user_id = user.id,
        token_hash = token_hash,
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes),
        token_type = token_type
    )

    
    await UserTokenRepository.create_token(confirm_token, db)
    
    await db.commit()
    
    return token_value, token_hash
    
async def delete_token_service(token_value: str, db: Annotated[AsyncSession, Depends(get_session)]) -> User:
    token_hash = hash_token(token_value)
    
    token = await UserTokenRepository.get_token(token_hash, db)
    
    if not token or not verify_token(token_value, token.token_hash):
        raise Authentication("Invalid or expired refresh token")
    
    if await UserTokenRepository.is_expired(token, db):
        await UserTokenRepository.delete_token(token, db)
        
        await db.commit()
        
        raise InvalidToken("Refresh token has expired")
    
    user_id = token.user_id
    
    user = await UserRepository.get_user_by_id(cast(UUID, user_id), db)
    
    if not user: 
        raise Authentication("User not found")
    
    await UserTokenRepository.delete_token(token, db)
        
    await db.commit()
    
    return user
    
async def send_email_confirmation_service(email: str, db: Annotated[AsyncSession, Depends(get_session)]):

    confirm_token_value, hash = await create_token_service(email, "verification",db)

    confirmation_link = f"http://{settings.domain}/api/auth/confirm-email?token={confirm_token_value}"
    
    try:
        result = resend.Emails.send({
            "from": settings.from_email,
            "to": email,
            "subject": "Подтверждение электронной почты",
            "html": f"Пожалуйста, подтвердите вашу электронную почту, кликнув на следующую ссылку: {confirmation_link}"
            })
        
        return EmailResponseDTO(success=True, id=result["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send confirmation email")

async def send_recovery_token_service(email: str, db: Annotated[AsyncSession, Depends(get_session)]):
    
    user = await UserRepository.get_user_by_email(email, db)
    
    if not user:
        raise Authentication("Invalid or expired reset token")
    
    await UserTokenRepository.delete_recovery_token(cast(UUID, user.id), db)
    
    confirm_token_value = await create_token_service(email, "recovery",db)
    
    try:
        result = resend.Emails.send({
            "from": settings.from_email,
            "to": email,
            "subject": "Восстановление доступа к аккаунту",
            "html": f"Пожалуйста, введите токен для сброса пароля: {confirm_token_value} Время действия: 30 минут"
            })
        
        return EmailResponseDTO(success=True, id=result["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send confirmation email")

async def reset_password_service(token: str, password: str, db: Annotated[AsyncSession, Depends(get_session)]):
    token_hash = hash_token(token)
    
    reset_token =  await UserTokenRepository.get_token(token_hash, db)
    
    if not reset_token:
        raise InvalidToken("Invalid or expired reset token")
        
    if await UserTokenRepository.is_expired(reset_token, db):
        raise InvalidToken("Invalid or expired reset token")
    
    user_id = reset_token.user_id
    
    user = await UserRepository.get_user_by_id(cast(UUID, user_id), db)
    
    if not user:
        raise InvalidToken("Invalid or expired reset token")
    
    password_hash = hash_password(password)
    
    await UserRepository.update_user({"password_hash": password_hash}, user, db)
    
    await db.commit()
    