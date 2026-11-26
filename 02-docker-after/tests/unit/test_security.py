import threading
import time

import anyio
import jwt
import pytest
from pydantic import ValidationError

from erudio.core import security
from erudio.core.config import Settings
from erudio.core.security import (
    MAX_CONCURRENT_HASHES,
    TokenPair,
    decode_token,
    hash_password,
    hash_password_async,
    issue_tokens,
    verify_password,
)
from erudio.models.user import User

ARGON2ID = "$argon2id$v=19$m=65536,t=3,p=4$"
LEANDRO_HASH = ARGON2ID + "oMW5+s5nhG9AjFtTvva1Ig$NaWRy1R/rpDLqOd/LF7Y0v7fx/l0umVOLy2As2RrCzE"
SECRET = "unit-test-secret-with-at-least-32-bytes"


def test_the_seeded_hash_is_verified() -> None:
    assert verify_password("admin123", LEANDRO_HASH)
    assert not verify_password("admin124", LEANDRO_HASH)
    assert not verify_password("", LEANDRO_HASH)


def test_the_hash_is_argon2id() -> None:
    hashed = hash_password("s3cret")

    assert hashed.startswith(ARGON2ID)
    assert verify_password("s3cret", hashed)
    assert not verify_password("other", hashed)
    assert "s3cret" not in hashed


def test_hashes_are_salted() -> None:
    assert hash_password("same") != hash_password("same")


@pytest.mark.parametrize(
    "stored",
    [
        "",
        "zz",
        "$argon2id$",
        "$argon2id$v=19$m=65536,t=3,p=4$abcd$abcd",
        # the Spring PBKDF2 format the port used before the migration 0020
        "{pbkdf2}1e3cdeeaaaeeda173ff6d002e7cb5e3f91ebc354dcff52156c9eaba1793a3a5e5bee306c11099e22",
        "1e3cdeeaaaeeda173ff6d002e7cb5e3f91ebc354dcff52156c9eaba1793a3a5e5bee306c11099e22",
    ],
)
def test_malformed_hashes_never_match(stored: str) -> None:
    assert not verify_password("anything", stored)


async def test_hashing_in_flight_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    lock = threading.Lock()
    running = peak = 0
    real = security.hash_password

    def counted(password: str) -> str:
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        try:
            return real(password)
        finally:
            with lock:
                running -= 1

    monkeypatch.setattr(security, "hash_password", counted)

    async with anyio.create_task_group() as group:
        for index in range(MAX_CONCURRENT_HASHES * 3):
            group.start_soon(hash_password_async, f"password-{index}")

    assert peak <= MAX_CONCURRENT_HASHES


def tokens(validity_ms: int = 3_600_000, secret: str = SECRET) -> TokenPair:
    return issue_tokens(
        "leandro", ["ADMIN", "MANAGER"], secret=secret, validity_ms=validity_ms, issuer="http://h"
    )


def test_the_access_token_carries_the_java_claims() -> None:
    claims = decode_token(tokens().access_token, secret=SECRET, access=True)

    assert claims["sub"] == "leandro"
    assert claims["roles"] == ["ADMIN", "MANAGER"]
    assert claims["iss"] == "http://h"
    assert claims["exp"] - claims["iat"] == 3600
    assert set(claims) == {"roles", "iat", "exp", "sub", "iss"}


def test_the_refresh_token_lasts_three_times_longer_and_has_no_issuer() -> None:
    claims = decode_token(tokens().refresh_token, secret=SECRET, access=False)

    assert claims["exp"] - claims["iat"] == 3 * 3600
    assert set(claims) == {"roles", "iat", "exp", "sub"}


def test_tokens_are_not_interchangeable() -> None:
    pair = tokens()

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(pair.refresh_token, secret=SECRET, access=True)
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(pair.access_token, secret=SECRET, access=False)


def test_created_and_expiration_are_one_validity_apart() -> None:
    pair = tokens(validity_ms=90_000)

    assert (pair.expiration - pair.created).total_seconds() == 90


def test_expired_and_tampered_tokens_are_rejected() -> None:
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(tokens(validity_ms=-60_000).access_token, secret=SECRET, access=True)
    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(tokens().access_token, secret=SECRET + "x", access=True)
    tampered = tokens().access_token[:-2] + (
        "aa" if not tokens().access_token.endswith("aa") else "bb"
    )
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(tampered, secret=SECRET, access=True)


def test_a_token_without_the_required_claims_is_rejected() -> None:
    bare = jwt.encode({"sub": "leandro"}, SECRET, algorithm="HS256")

    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_token(bare, secret=SECRET, access=True)


def test_the_none_algorithm_is_rejected() -> None:
    forged = jwt.encode(
        {"sub": "leandro", "iss": "x", "iat": int(time.time()), "exp": int(time.time()) + 60},
        "",
        algorithm="none",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(forged, secret=SECRET, access=True)


def test_short_secrets_are_refused() -> None:
    with pytest.raises(jwt.InvalidKeyError):
        tokens(secret="short")
    with pytest.raises(ValidationError):
        Settings(database_url="mysql+asyncmy://x@h/d", jwt_secret_key="short")


@pytest.mark.parametrize(
    ("enabled", "expired", "locked", "credentials", "active"),
    [
        (True, True, True, True, True),
        (False, True, True, True, False),
        (True, False, True, True, False),
        (True, True, False, True, False),
        (True, True, True, False, False),
        (None, True, True, True, False),
    ],
)
def test_only_fully_enabled_accounts_are_active(
    enabled: bool | None, expired: bool, locked: bool, credentials: bool, active: bool
) -> None:
    user = User(
        user_name="u",
        password="p",
        enabled=enabled,
        account_non_expired=expired,
        account_non_locked=locked,
        credentials_non_expired=credentials,
    )

    assert user.is_active is active
