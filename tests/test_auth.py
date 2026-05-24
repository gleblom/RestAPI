import datetime
import pytest

from src.security import (
    hash_password,
    verify_password,
    create_token,
    verify_token,
    create_access_token,
    decode_access_token,
    get_refresh_token_expire_time,
)


def test_hash_and_verify_password():
    pw = "S3cureP@ssw0rd"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_verify_token():
    raw, hashed = create_token()
    assert verify_token(raw, hashed)
    assert not verify_token("badtoken", hashed)


def test_create_access_and_decode_token():
    token = create_access_token({"sub": "test-sub"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "test-sub"
    assert payload.get("token_type") == "access"


def test_decode_invalid_token():
    token = create_access_token({"sub": "t"})
    bad = token + "x"
    assert decode_access_token(bad) is None


def test_get_refresh_token_expire_time_future():
    exp = get_refresh_token_expire_time()
    assert exp > datetime.datetime.now(datetime.timezone.utc)
