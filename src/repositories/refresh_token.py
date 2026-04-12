
from datetime import UTC, datetime
from typing import cast


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from src.models.users import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    async def create_refresh_token(refresh_token: RefreshToken, db: AsyncSession) -> RefreshToken:
        db.add(refresh_token)
        await db.flush()
        return refresh_token
    
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