
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User
from models.views import VUser


class UserRepository:
    @staticmethod
    async def get_user_by_email(email: str,  db: AsyncSession) -> User | None:
        
        result = await db.execute(select(User).where(func.lower(User.email) == func.lower(email)))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id( user_id: UUID, db: AsyncSession) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        
        return result.scalar_one_or_none()

    
    @staticmethod
    async def create_user(user: User, db: AsyncSession) -> User:
        db.add(user)       
        await db.flush()
        
        return user
    
    @staticmethod
    async def update_user(user_data: dict, user: User, db: AsyncSession) -> User:

        for k, v in user_data.items():
            setattr(user, k, v)

        await db.flush()
        
        return user