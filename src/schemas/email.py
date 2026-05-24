from pydantic import BaseModel, EmailStr, Field


class EmailRequestDTO(BaseModel):# @IgnoreException
    to: EmailStr = Field(..., min_length=5, max_length=50)
    subject: str
    body: str

class EmailResponseDTO(BaseModel):# @IgnoreException
    success: bool
    id: str    