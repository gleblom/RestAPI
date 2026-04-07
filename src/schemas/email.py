from pydantic import BaseModel, EmailStr


class EmailRequestDTO(BaseModel):
    to: EmailStr
    subject: str
    body: str

class EmailResponseDTO(BaseModel):
    success: bool
    id: str    