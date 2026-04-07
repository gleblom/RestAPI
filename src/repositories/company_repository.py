from uuid import UUID

from sqlalchemy import select

from models.dictionaries import Company

from sqlalchemy.ext.asyncio import AsyncSession


class CompanyRepository:
    @staticmethod
    async def create_company(company: Company, db: AsyncSession) -> Company:
        db.add(Company)
        
        await db.flush()
        
        return company
    
    @staticmethod
    async def get_company(comapny_id: UUID, db: AsyncSession) -> Company | None:
        result = await db.execute(select(Company).where(Company.id == comapny_id))

        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_company_by_director(director_id: UUID, db: AsyncSession) -> Company | None:
        result = await db.execute(select(Company).where(Company.director_id == director_id))

        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_company(company_data: dict, company: Company, db: AsyncSession):
        
        for k, v in company_data.items():
            setattr(company, k, v)
        await db.flush()
        
        return company
    
    