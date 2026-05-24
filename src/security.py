import base64
from datetime import UTC, datetime, timedelta
from enum import Enum
import hashlib
import hmac
import secrets
from typing import Annotated, Any, List, Literal, cast
from uuid import UUID, uuid4
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models.views import VUser
from src.repositories.profile_repository import ProfileRepository
from src.config import Config

settings = Config() # type: ignore

password_hash = PasswordHash.recommended()

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

def generate_challenge() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

class AuthLevel(str, Enum):
    PRIMARY = "primary"
    FULL = "full"


class TokenType(str, Enum):
    ACCESS = "access"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    *,
    auth_level: AuthLevel = AuthLevel.FULL,
) -> str:
    to_encode = data.copy()

    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))

    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": str(uuid4()),
            "token_type": TokenType.ACCESS.value,
            "auth_level": auth_level.value,
        }
    )

    return jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub", "token_type", "auth_level"]},
        )
    except JWTError:
        return None

    if payload.get("token_type") != TokenType.ACCESS.value:
        return None

    if payload.get("auth_level") not in {AuthLevel.PRIMARY.value, AuthLevel.FULL.value}:
        return None

    return payload
    
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

async def _get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_session)],
    *,
    require_auth_level: Literal["primary", "full"],
):
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    auth_level = payload.get("auth_level")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if require_auth_level == "full" and auth_level != AuthLevel.FULL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Two-factor authentication required",
        )

    user = await ProfileRepository.get_profile_by_id(cast(UUID, user_id), db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user



async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    return await _get_current_user(token, db, require_auth_level="full")

async def get_current_user_pending_2fa(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    return await _get_current_user(token, db, require_auth_level="primary")

CurrentUser = Annotated[VUser, Depends(get_current_user)]

class RoleChecker:
    def  __init__(self, allowed_roles: List[int]) -> None:
        
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: VUser = Depends(get_current_user)) -> VUser:
        if current_user.role_id not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return current_user