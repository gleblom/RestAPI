from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from typing import Annotated, Any, List, cast
from uuid import UUID
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models.users import User
from models.views import VUser
from repositories.profile_repository import ProfileRepository
from src.config import Config

settings = Config() # type: ignore

password_hash = PasswordHash.recommended()

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    
    if(expires_delta):
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
                             to_encode, 
                             settings.secret_key.get_secret_value(), 
                             algorithm=settings.algorithm
                             )
    
    return encoded_jwt

def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
                             token, 
                             settings.secret_key.get_secret_value(), 
                             algorithms=[settings.algorithm],
                             options={"require": ["exp", "sub"]},
                             )
    
    except JWTError:
       return None  
    else:
        return payload.get("sub")
    
def hash_token(token: str) -> str:
    return hmac.new(
        settings.secret_key.get_secret_value().encode(),
        token.encode(),
        hashlib.sha256
    ).hexdigest()    
    
def create_token() -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(32)
    
    token_hash = hash_token(raw_token)
    
    return raw_token, token_hash

def verify_token(plain_token: str, hashed_token: str):
    return hmac.compare_digest(hash_token(plain_token), hashed_token)

def get_refresh_token_expire_time() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days) 


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_session)]
):
    user_id = decode_access_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await ProfileRepository.get_profile_by_id(cast(UUID,user_id), db)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user

CurrentUser = Annotated[VUser, Depends(get_current_user)]

class RoleChecker:
    def  __init__(self, allowed_roles: List[int]) -> None:
        
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: VUser = Depends(get_current_user)) -> Any:
        if current_user.role_id in self.allowed_roles:
            return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to perfrom this action"
        )