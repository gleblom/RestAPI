from pydantic import BaseModel, EmailStr


class EmailRequestDTO(BaseModel):# @IgnoreException
    to: EmailStr
    subject: str
    body: str

class EmailResponseDTO(BaseModel):# @IgnoreException
    success: bool
    id: str    