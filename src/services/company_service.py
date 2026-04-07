from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from exceptions import AlreadyExists
from models.dictionaries import Company
from repositories.company_repository import CompanyRepository

async def add_company_service(
    db: Annotated[AsyncSession, Depends(get_session)], 
    company_name: str,
    director_id: UUID
    ):
    
    existed_company = await CompanyRepository.get_company_by_director(cast(UUID, director_id), db)
    
    if existed_company:
        raise AlreadyExists("A company with such a director already exists.")
    
    company = Company(
        company_name = company_name,
        director_id = director_id
    )
    
    try:
        await CompanyRepository.create_company(company, db)
        await db.commit()
        await db.refresh(company)
        
        return company
    except Exception as e:
        await db.rollback()
        raise e
