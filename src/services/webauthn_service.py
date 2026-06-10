from __future__ import annotations

import base64
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import parse_authentication_credential_json, parse_registration_credential_json
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)
from webauthn.helpers.exceptions import InvalidAuthenticationResponse

from src.schemas.webauthn import PasskeyStatusDTO
from src.config import Config
from src.models.webauthn import WebAuthnChallenge, WebAuthnCredential
from src.repositories.user_repository import UserRepository
from src.security import AuthLevel, CurrentUser, create_access_token
from src.services.user_service import create_token, get_refresh_token_expire_time
from src.models.users import RefreshToken
from src.repositories.refresh_token import RefreshTokenRepository


CHALLENGE_TTL_SECONDS = 300

settings = Config() # type: ignore

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _now() -> datetime:
    return datetime.now(UTC)


async def _store_challenge(
    db: AsyncSession,
    *,
    user_id: UUID | None = None,
    purpose: str,
    challenge: bytes,
) -> WebAuthnChallenge:
    challenge_row = WebAuthnChallenge(
        user_id=user_id,
        purpose=purpose,
        challenge_b64=_b64url_encode(challenge),
        expires_at=_now() + timedelta(seconds=CHALLENGE_TTL_SECONDS),)
    
    db.add(challenge_row)
    
    await db.flush()
    
    return challenge_row


async def _get_active_challenge(db: AsyncSession, user_id: UUID, purpose: str) -> WebAuthnChallenge:
    stmt = (
        select(WebAuthnChallenge)
        .where(
            WebAuthnChallenge.user_id == user_id,
            WebAuthnChallenge.purpose == purpose,
            WebAuthnChallenge.consumed_at.is_(None),
            WebAuthnChallenge.expires_at > _now(),
        )
        .order_by(WebAuthnChallenge.created_at.desc())
        .limit(1)
        .with_for_update()
    )
    result = await db.execute(stmt)
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Challenge expired or missing")
    return challenge


async def _consume_challenge(db: AsyncSession, challenge: WebAuthnChallenge) -> None:
    challenge.consumed_at = _now()
    await db.flush()


async def generate_webauthn_registration_options_service(
    current_user,
    db: AsyncSession,
) -> dict:
    user = await UserRepository.get_user_by_id(cast(UUID, current_user.user_id), db)
    if not user:
        fake_challenge = secrets.token_bytes(32)
        options = generate_authentication_options(
            rp_id=settings.webauthn_rp_id,
            challenge=fake_challenge,
            allow_credentials=[], 
    )
        return json.loads(options_to_json(options))

    existing_credentials_stmt = select(WebAuthnCredential).where(
        WebAuthnCredential.user_id == user.id,
        WebAuthnCredential.is_revoked.is_(False),
    )
    result = await db.execute(existing_credentials_stmt)
    existing_credentials = result.scalars().all()

    challenge = secrets.token_bytes(32)
    challenge_row = await _store_challenge(db,  user_id=cast(UUID, user.id), purpose="register", challenge=challenge)
    await db.flush()

    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=cast(UUID, user.id).bytes,
        user_name=user.email,
        user_display_name=user.email,
        challenge=challenge,
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id_b64))
            for c in existing_credentials
        ],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        attestation=AttestationConveyancePreference.NONE,
    )

    await db.commit()
    return {
        "challenge_id": str(challenge_row.id),
        "options": json.loads(options_to_json(options))
    }


async def finish_webauthn_registration_service(
    current_user: CurrentUser,
    payload: dict,
    db: AsyncSession,
) -> dict:
    user = await UserRepository.get_user_by_id(cast(UUID, current_user.user_id), db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    challenge_row = await _get_active_challenge(db, cast(UUID, user.id), "register")
    expected_challenge = base64url_to_bytes(challenge_row.challenge_b64)

    credential = parse_registration_credential_json(payload["credential"])

    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origins,
            require_user_verification=True,
        )
    except InvalidAuthenticationResponse as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    credential_id_b64 = _b64url_encode(verification.credential_id)
    public_key_b64 = _b64url_encode(verification.credential_public_key)
    device_id=payload.get("device_id"),
    device_name=payload.get("device_name"),
    db.add(
        WebAuthnCredential(
            user_id=user.id,
            credential_id_b64=credential_id_b64,
            public_key_b64=public_key_b64,
            sign_count=verification.sign_count,
            transports_json=payload["credential"].get("response", {}).get("transports", []),
            is_platform=payload["credential"].get("authenticatorAttachment") == "platform",
            device_id=payload.get("device_id"),
            device_name=payload.get("device_name"),
        )
    )
    # await UserRepository.update_user(
    #     {"passkey_enabled": True},
    #     user,
    #     db
    # )

    await _consume_challenge(db, challenge_row)
    await db.commit()

    return {"status": "ok"}


async def generate_webauthn_login_options_service(
 db: AsyncSession,
) -> dict:
        
    challenge = secrets.token_bytes(32)

    challenge_row = await _store_challenge(db, purpose="login", challenge=challenge)

    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        challenge=challenge,
        allow_credentials=[],
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    await db.commit() 
    
    return {
        "challenge_id": str(challenge_row.id),
        "options": json.loads(options_to_json(options))
    }


async def finish_webauthn_login_service(
    payload: dict,
    db: AsyncSession,
) -> tuple[str, str]:
    challenge_id = payload.get("challenge_id")
    credential_payload = payload["credential"]
    credential_id_b64 = credential_payload["id"]
    
    challenge_row = await db.get(WebAuthnChallenge, challenge_id)
    
    if not challenge_row or challenge_row.consumed_at or challenge_row.expires_at < _now():
        raise HTTPException(status_code=400, detail="Challenge expired or invalid")

    cred_stmt = select(WebAuthnCredential).where(
        WebAuthnCredential.credential_id_b64 == credential_id_b64,
        WebAuthnCredential.is_revoked.is_(False),
    )

    webauthn_cred = (await db.execute(cred_stmt)).scalar_one_or_none()

    if not webauthn_cred:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credential")
    

    user = await UserRepository.get_user_by_id(cast(UUID, webauthn_cred.user_id), db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    expected_challenge = base64url_to_bytes(challenge_row.challenge_b64)
    credential = parse_authentication_credential_json(credential_payload)

    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origins,
            credential_public_key=base64url_to_bytes(webauthn_cred.public_key_b64),
            credential_current_sign_count=webauthn_cred.sign_count,
            require_user_verification=True,
        )
    except InvalidAuthenticationResponse as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    webauthn_cred.sign_count = verification.new_sign_count
    webauthn_cred.last_used_at = _now()
    await _consume_challenge(db, challenge_row)

    access_token = create_access_token(
        {"sub": str(user.id), "amr": ["webauthn"]},
        auth_level=AuthLevel.FULL,
    )
    
    jti = uuid4()

    refresh_token_value, hashed_token_value = create_token()
    refresh_token = RefreshToken(
        token_hash=hashed_token_value,
        user_id=user.id,
        auth_level=AuthLevel.FULL.value,
        expires_at=get_refresh_token_expire_time(),
        is_revoked=False,
        jti=jti
    )
    await RefreshTokenRepository.create_refresh_token(refresh_token, db)

    await db.commit()
    return access_token, refresh_token_value

async def get_passkey_status_service(
    user_id: UUID,
    device_id: str,
    db: AsyncSession,
) -> PasskeyStatusDTO:
    stmt = select(WebAuthnCredential).where(
        WebAuthnCredential.user_id == user_id,
        WebAuthnCredential.is_revoked.is_(False),
    )
    creds = (await db.execute(stmt)).scalars().all()

    active_count = len(creds)
    current_device_has_passkey = any((c.device_id == device_id) for c in creds)

    state = 'None'
    if active_count == 0:
        state = "disabled"
    elif current_device_has_passkey:
        state = "enabled_this_device"
        
    return PasskeyStatusDTO(
        state=state,
        active_count=active_count,
        current_device_has_passkey=current_device_has_passkey,
    )