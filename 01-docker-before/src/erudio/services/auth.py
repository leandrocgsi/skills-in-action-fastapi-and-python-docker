from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from erudio.core.config import Settings
from erudio.core.errors import (
    ConflictError,
    ForbiddenError,
    InvalidCredentialsError,
    InvalidJwtError,
    ResourceNotFoundError,
)
from erudio.core.security import (
    DUMMY_HASH,
    InvalidTokenError,
    decode_token,
    hash_password_async,
    issue_tokens,
    verify_password_async,
)
from erudio.models.user import User
from erudio.repositories import user as users
from erudio.schemas.auth import CredentialsRequest, TokenResponse

BEARER = "Bearer "


def _token_for(user: User, settings: Settings, issuer: str) -> TokenResponse:
    tokens = issue_tokens(
        user.user_name,
        user.roles,
        secret=settings.jwt_secret_key,
        validity_ms=settings.jwt_expire_milliseconds,
        issuer=issuer,
    )
    return TokenResponse(
        username=user.user_name,
        authenticated=True,
        created=tokens.created,
        expiration=tokens.expiration,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )


async def sign_in(
    session: AsyncSession, settings: Settings, credentials: CredentialsRequest, issuer: str
) -> TokenResponse:
    user = await users.get_by_username(session, credentials.username)
    stored = user.password if user is not None else DUMMY_HASH
    matches = await verify_password_async(credentials.password, stored)
    if user is None or not matches or not user.is_active:
        raise InvalidCredentialsError
    return _token_for(user, settings, issuer)


async def refresh(
    session: AsyncSession, settings: Settings, username: str, authorization: str, issuer: str
) -> TokenResponse:
    user = await users.get_by_username(session, username)
    if user is None:
        raise ResourceNotFoundError(f"Username {username} not found!")
    if not authorization.startswith(BEARER):
        raise InvalidJwtError
    try:
        claims = decode_token(
            authorization.removeprefix(BEARER).strip(), secret=settings.jwt_secret_key, access=False
        )
    except InvalidTokenError as error:
        raise InvalidJwtError from error
    if not user.is_active:
        raise InvalidJwtError
    if claims["sub"] != username:
        raise ForbiddenError("The token does not belong to this user!")
    return _token_for(user, settings, issuer)


async def create_user(session: AsyncSession, credentials: CredentialsRequest) -> User:
    if await users.get_by_username(session, credentials.username) is not None:
        raise ConflictError(f"Username {credentials.username} already exists!")
    user = User(
        user_name=credentials.username,
        full_name=credentials.fullname,
        password=await hash_password_async(credentials.password),
        account_non_expired=True,
        account_non_locked=True,
        credentials_non_expired=True,
        enabled=True,
    )
    users.add(session, user)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise ConflictError(f"Username {credentials.username} already exists!") from error
    await session.refresh(user)
    return user
