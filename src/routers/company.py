
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated, cast
from uuid import UUID

from src.database import get_session
from src.exceptions import AlreadyExists, NotFound
from src.schemas.dictionaries import CompanyCreateDTO, CompanyReadDTO, CompanyUpdateDTO
from src.security import CurrentUser
from src.services.company_service import add_company_service, update_company_service

router = APIRouter(
    prefix="/company",
    tags=["company"],
)      
    
@router.post("", status_code=status.HTTP_201_CREATED, response_model=CompanyReadDTO)
async def create_company(db: Annotated[AsyncSession, Depends(get_session)], company: CompanyCreateDTO):
    try:
       created_company = await add_company_service(db, company.company_name, company.director_id)
       
       return created_company
    except AlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Database error")
        
@router.put("", status_code=status.HTTP_200_OK, response_model=CompanyReadDTO)
async def update_company(db: Annotated[AsyncSession, Depends(get_session)], current_user: CurrentUser, company: CompanyUpdateDTO):
    try:
        updated_company = await update_company_service(db, current_user, company.company_id, company.company_name)
        
        return updated_company
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Database error")