# otp_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import RefreshToken
from src.repositories.refresh_token import RefreshTokenRepository
from src.security import AuthLevel, create_access_token, create_token, get_refresh_token_expire_time
from src.config.main import Config
from src.schemas.users import OtpDTO, UserTokenDTO
from src.repositories.user_repository import UserRepository


OTP_VALID_WINDOW = 1          # допускаем ±1 шаг времени
MAX_OTP_ATTEMPTS = 5
LOCKOUT_SECONDS = 300         # 5 минут

settings = Config()  # type: ignore
fernet_key = settings.fernet_key.encode()
fernet = Fernet(fernet_key)


def encrypt_secret(secret: str) -> str:
    return fernet.encrypt(secret.encode()).decode()


def decrypt_secret(secret_enc: str) -> str:
    try:
        return fernet.decrypt(secret_enc.encode()).decode()
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP secret cannot be decrypted",
        )


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _is_locked(user) -> bool:
    locked_until = getattr(user, "otp_locked_until", None)
    return locked_until is not None and locked_until > now_utc()


async def _register_failed_attempt(user, db: AsyncSession) -> None:
    attempts = int(getattr(user, "otp_failed_attempts", 0) or 0) + 1
    locked_until = getattr(user, "otp_locked_until", None)

    updates = {"otp_failed_attempts": attempts, "otp_locked_until": locked_until}

    if attempts >= MAX_OTP_ATTEMPTS:
        updates["otp_locked_until"] = now_utc() + timedelta(seconds=LOCKOUT_SECONDS)
        updates["otp_failed_attempts"] = 0

    await UserRepository.update_user(updates, user, db)
    await db.commit()


async def _clear_otp_state(user, db: AsyncSession, *, last_used_step: int | None = None) -> None:
    updates = {
        "otp_failed_attempts": 0,
        "otp_locked_until": None,
    }
    if last_used_step is not None:
        updates["otp_last_used_step"] = last_used_step

    await UserRepository.update_user(updates, user, db)
    await db.commit()


def _verify_totp(
    secret: str,
    token: str,
    *,
    last_used_step: int | None = None,
    valid_window: int = OTP_VALID_WINDOW,
) -> tuple[bool, int | None]:
    totp = pyotp.TOTP(secret)
    now = now_utc()

    for offset in range(-valid_window, valid_window + 1):
        candidate_time = now + timedelta(seconds=offset * totp.interval)
        candidate_token = totp.at(candidate_time)
        if candidate_token == token:
            candidate_step = int(totp.timecode(candidate_time))
            if last_used_step is not None and candidate_step <= last_used_step:
                return False, None
            return True, candidate_step

    return False, None


async def generate_otp_service(email: str, db: AsyncSession) -> OtpDTO:
    user = await UserRepository.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Новый секрет создается только на сервере
    otp_base32 = pyotp.random_base32()
    otp_secret_enc = encrypt_secret(otp_base32)

    # QR / provisioning URI для приложения-аутентификатора
    otp_auth_url = pyotp.TOTP(otp_base32).provisioning_uri(name=email, issuer_name="dms")

    # Секрет хранится в pending-состоянии, пока пользователь не подтвердит код
    await UserRepository.update_user(
        {
            "otp_pending_secret_enc": otp_secret_enc,
            "otp_pending_verified": False,
            "otp_pending_created_at": now_utc(),
            "otp_enabled": False,
            "otp_verified": False,
            "otp_failed_attempts": 0,
            "otp_locked_until": None,
        },
        user,
        db,
    )
    await db.commit()

    return OtpDTO(
        otp_base32=otp_base32,
        otp_auth_url=otp_auth_url,
    )


async def confirm_otp_service(token: str, user_id: UUID, db: AsyncSession):
    user = await UserRepository.get_user_by_id(user_id, db)
    if not user or not getattr(user, "otp_pending_secret_enc", None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if _is_locked(user):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="OTP temporarily locked")

    secret = decrypt_secret(user.otp_pending_secret_enc)
    ok, step = _verify_totp(
        secret,
        token,
        last_used_step=getattr(user, "otp_last_used_step", None),
    )

    if not ok:
        await _register_failed_attempt(user, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    # Переносим pending -> active
    await UserRepository.update_user(
        {
            "otp_secret_enc": user.otp_pending_secret_enc,
            "otp_pending_secret_enc": None,
            "otp_enabled": True,
            "otp_verified": True,
            "otp_pending_verified": True,
            "otp_last_used_step": step,
            "otp_failed_attempts": 0,
            "otp_locked_until": None,
        },
        user,
        db,
    )
    await db.commit()
    
    return {"otp_verified": True}



async def validate_otp_service(token: str, user_id: UUID, db: AsyncSession):
    user = await UserRepository.get_user_by_id(user_id, db)
    if not user or not getattr(user, "otp_enabled", False) or not getattr(user, "otp_secret_enc", None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if _is_locked(user):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="OTP temporarily locked")

    secret = decrypt_secret(user.otp_secret_enc)
    ok, step = _verify_totp(
        secret,
        token,
        last_used_step=getattr(user, "otp_last_used_step", None),
    )

    if not ok:
        await _register_failed_attempt(user, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    await _clear_otp_state(user, db, last_used_step=step)
    
    access_token = create_access_token(
        {"sub": str(user.id)},
        auth_level=AuthLevel.FULL,
    )

 
    refresh_token_value, hashed_token_value = create_token()

    jti = uuid4()

    refresh_token = RefreshToken(
        token_hash=hashed_token_value,
        user_id=user.id,
        auth_level="full",
        expires_at=get_refresh_token_expire_time(),
        is_revoked=False,
        jti=jti,
        parent_jti=None
    )

    await RefreshTokenRepository.create_refresh_token(refresh_token, db)
    await db.commit()

    return UserTokenDTO(
        access_token = access_token,
        token_type = "bearer",
        refresh_token = refresh_token_value,
    )
    



async def disable_otp_service(user_id: UUID, db: AsyncSession):
    user = await UserRepository.get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await UserRepository.update_user(
        {
            "otp_enabled": False,
            "otp_verified": False,
            "otp_secret_enc": None,
            "otp_pending_secret_enc": None,
            "otp_pending_verified": False,
            "otp_last_used_step": None,
            "otp_failed_attempts": 0,
            "otp_locked_until": None,
        },
        user,
        db,
    )
    await db.commit()
    return {"otp_enabled": False}
