
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select

from src.models.users import User, UserToken

from sqlalchemy.ext.asyncio import AsyncSession

class UserTokenRepository:
    @staticmethod
    async def create_token(token: UserToken, db: AsyncSession) -> UserToken:
        db.add(token)
        await db.flush()
        
        return token
    
    @staticmethod
    async def get_token(token_hash: str, db: AsyncSession) -> UserToken | None:
        stmt = select(UserToken).where(UserToken.token_hash == token_hash)
        result = await db.execute(stmt)
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_token(token: UserToken, db: AsyncSession):
      await db.delete(token)
      
      await db.flush()
    
    @staticmethod 
    async def delete_recovery_token(user_id: UUID, db: AsyncSession):
         result = await db.execute(
             select(UserToken)
             .where(
                 UserToken.user_id == user_id and 
                 UserToken.token_type == "recovery")
             )
         token = result.scalar_one_or_none()
         
         await db.delete(token)
         
         await db.flush()
        
    
    @staticmethod 
    async def is_expired(token: UserToken, db: AsyncSession):
        return cast(datetime, token.expires_at) < datetime.now(UTC)