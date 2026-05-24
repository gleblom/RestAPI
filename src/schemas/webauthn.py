from __future__ import annotations
from typing import Any
import uuid

from pydantic import BaseModel



class WebAuthnLoginOptionsDTO(BaseModel):

    email: str | None = None 


class WebAuthnFinishDTO(BaseModel):

    challenge_id: uuid.UUID 
    
    credential: dict[str, Any]