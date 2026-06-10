from __future__ import annotations
from typing import Any, Literal
import uuid

from pydantic import BaseModel



class WebAuthnLoginOptionsDTO(BaseModel):

    email: str | None = None 


class WebAuthnFinishDTO(BaseModel):

    challenge_id: uuid.UUID 
    
    credential: dict[str, Any]
    
    device_name: str
    device_id: str
    
class PasskeyStatusDTO(BaseModel):
    state: str
    active_count: int
    current_device_has_passkey: bool