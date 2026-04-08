from uuid import UUID

from pydantic import BaseModel


class CompanyReadDTO(BaseModel):
    company_name: str
    director_id: UUID

class CompanyCreateDTO(BaseModel):
    company_name: str
    director_id: UUID
    
class CompanyUpdateDTO(BaseModel):
    company_name: str
    company_id: UUID