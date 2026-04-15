from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.user_repository import UserRepository
from src.database import get_session
from src.exceptions import AlreadyExists, NotFound
from src.models.dictionaries import Company
from src.repositories.company_repository import CompanyRepository
from src.schemas.dictionaries import CompanyUpdateDTO
from src.security import CurrentUser

async def add_company_service(
    db: Annotated[AsyncSession, Depends(get_session)], 
    name: str,
    director_id: UUID
    ):
    
    director = await UserRepository.get_user_by_id(director_id, db)
    
    if not director:
        raise NotFound("User with this id not found")
    
    existed_company = await CompanyRepository.get_company_by_director(cast(UUID, director_id), db)
    
    if existed_company:
        raise AlreadyExists("A company with such a director already exists.")
    
    company = Company(
        name = name,
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

async def update_company_service(
    db: Annotated[AsyncSession, Depends(get_session)], 
    current_user: CurrentUser, 
    company_id: UUID,
    company_name: str):
    
    company = await CompanyRepository.get_company(company_id, db)
    
    if not company:
        raise NotFound()
    
    if company.director_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this company",
        )
    try:
        updated_company = await CompanyRepository.update_company({"company_name": company_name}, company, db)
        
        await db.commit()
        
        return updated_company

    except Exception as e:
        await db.rollback()
        raise e
    
    
    