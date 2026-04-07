from sqlalchemy import UUID, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dictionaries import Category, Role, RoleCategory
from models.views import VRoleCategory


class RoleRepository:
    
    @staticmethod
    async def create_role(role: Role, db: AsyncSession):
        db.add(role)
        
        await db.flush()
        
        return role
    
    @staticmethod
    async def get_roles_by_company(company_id: UUID, db: AsyncSession):
        result = await db.execute(select(Role).where(Role.company_id == company_id))
        
        return result.all()
    
    @staticmethod
    async def update_role(role_data: dict, role: Role, db: AsyncSession):
        
        for k, v in role_data.items():
            setattr(role, k, v)
            
        await db.flush()
        
        return role
    
    @staticmethod
    async def create_role_category(role_cateogry: RoleCategory, db: AsyncSession):
        db.add(role_cateogry)
        
        await db.flush()
        
        return role_cateogry
    
    @staticmethod
    async def get_role_categories_by_company(company_id: UUID, db: AsyncSession):
        result = await db.execute(select(VRoleCategory).where(VRoleCategory.company_id == company_id))
        
        return result.all()
    
    @staticmethod
    async def update_role_category(role_category_data: dict, role_category: RoleCategory, db: AsyncSession):
        
        for k, v in  role_category_data.items():
            setattr(role_category, k, v)
            
        await db.flush()
        
        return role_category
    
    @staticmethod
    async def get_categories(db: AsyncSession):
        result = await(db.execute(select(Category)))
        
        return result.all()