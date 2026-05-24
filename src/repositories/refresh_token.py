
from datetime import UTC, datetime
from typing import cast
from uuid import UUID


from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


from src.models.users import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    async def create_refresh_token( refresh_token: RefreshToken,db: AsyncSession,) -> None:
        db.add(refresh_token)
    
    @staticmethod
    async def get_token(token_hash:str, db: AsyncSession
    ) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def revoke_refresh_token(refresh_token: RefreshToken, db: AsyncSession) -> None:
        refresh_token.is_revoked = True  
        await db.flush()
        
    @staticmethod
    async def is_expired(refresh_token: RefreshToken) -> bool:
        return cast(datetime, refresh_token.expires_at) < datetime.now(UTC)
    
    @staticmethod
    async def revoke_all_user_tokens(user_id: UUID, db: AsyncSession):
        stmt = update(RefreshToken).where(RefreshToken.user_id == user_id).values(is_revoked = True)
        await db.execute(stmt)
        await db.commit();
    
    # @staticmethod
    # async def get_token_for_update(token_hash: str,db: AsyncSession,) -> RefreshToken | None:
    #     stmt = (
    #         select(RefreshToken)
    #         .where(RefreshToken.token_hash == token_hash)
    #         .with_for_update()
    #     )
    #     result = await db.execute(stmt)
    #     return result.scalar_one_or_none()