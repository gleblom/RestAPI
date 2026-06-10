from datetime import UTC, datetime
from typing import cast

from sqlalchemy import select

from src.models.documents import DocumentToken
from sqlalchemy.ext.asyncio import AsyncSession

class DocumentTokenRepository:
    @staticmethod
    async def create_token(token: DocumentToken, db: AsyncSession) -> DocumentToken:
        db.add(token)
        await db.flush()
        
        return token
    
    @staticmethod
    async def get_token(token_hash: str, db: AsyncSession) -> DocumentToken | None:
        stmt = select(DocumentToken).where(DocumentToken.token_hash == token_hash)
        result = await db.execute(stmt)
        
        return result.scalar_one_or_none()

      
    @staticmethod 
    async def is_expired(token: DocumentToken, db: AsyncSession):
        return cast(datetime, token.expires_at) < datetime.now(UTC)