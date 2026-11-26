import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import anyio
import anyio.to_thread
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

ALGORITHM = "HS256"
LEEWAY_SECONDS = 5
REFRESH_VALIDITY_FACTOR = 3
# Argon2id is memory-hard (64 MiB per hash with the defaults): bound the hashes in flight so a
# burst of sign-ins cannot exhaust the memory of the container.
MAX_CONCURRENT_HASHES = 4

_jwt = jwt.PyJWT(options={"enforce_minimum_key_length": True})
_hasher = PasswordHasher()
_hashing = anyio.CapacityLimiter(MAX_CONCURRENT_HASHES)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, stored: str) -> bool:
    try:
        return _hasher.verify(stored, password)
    except VerificationError, InvalidHashError:
        return False


DUMMY_HASH = hash_password(secrets.token_hex(16))


async def hash_password_async(password: str) -> str:
    return await anyio.to_thread.run_sync(hash_password, password, limiter=_hashing)


async def verify_password_async(password: str, stored: str) -> bool:
    return await anyio.to_thread.run_sync(verify_password, password, stored, limiter=_hashing)


@dataclass(frozen=True, slots=True)
class TokenPair:
    created: datetime
    expiration: datetime
    access_token: str
    refresh_token: str


def issue_tokens(
    username: str, roles: list[str], *, secret: str, validity_ms: int, issuer: str
) -> TokenPair:
    now = datetime.now(UTC).replace(microsecond=0)
    created = datetime.now(UTC)
    validity = timedelta(milliseconds=validity_ms)
    expiration = created + validity
    access = {
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + validity).timestamp()),
        "sub": username,
        "iss": issuer,
    }
    refresh = {
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + validity * REFRESH_VALIDITY_FACTOR).timestamp()),
        "sub": username,
    }
    return TokenPair(
        created=created,
        expiration=expiration,
        access_token=_jwt.encode(access, secret, algorithm=ALGORITHM),
        refresh_token=_jwt.encode(refresh, secret, algorithm=ALGORITHM),
    )


def decode_token(token: str, *, secret: str, access: bool) -> dict[str, Any]:
    required = ["exp", "iat", "sub", "iss"] if access else ["exp", "iat", "sub"]
    claims: dict[str, Any] = _jwt.decode(
        token,
        secret,
        algorithms=[ALGORITHM],
        leeway=LEEWAY_SECONDS,
        options={"require": required},
    )
    if not access and "iss" in claims:
        msg = "an access token is not a refresh token"
        raise jwt.InvalidTokenError(msg)
    return claims


InvalidTokenError = jwt.InvalidTokenError
