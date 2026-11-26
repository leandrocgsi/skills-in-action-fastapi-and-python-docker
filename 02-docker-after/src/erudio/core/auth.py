from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from erudio.core.config import Settings
from erudio.core.database import SessionDep
from erudio.core.dependencies import SettingsDep
from erudio.core.errors import AuthenticationRequiredError
from erudio.core.security import InvalidTokenError, decode_token
from erudio.models.user import User
from erudio.repositories import user as users

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="Bearer", description="JWT access token")


def authenticate_token(token: str | None, settings: Settings) -> Mapping[str, Any]:
    """Validates signature, issuer and expiry only; no database lookup."""
    if not token:
        raise AuthenticationRequiredError
    try:
        return decode_token(token, secret=settings.jwt_secret_key, access=True)
    except InvalidTokenError as error:
        raise AuthenticationRequiredError from error


def authenticate_request(request: Request, settings: Settings) -> None:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    authenticate_token(token.strip() if scheme.lower() == "bearer" else None, settings)


async def current_user(
    session: SessionDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    claims = authenticate_token(credentials.credentials if credentials else None, settings)
    user = await users.get_by_username(session, claims["sub"])
    if user is None or not user.is_active:
        raise AuthenticationRequiredError
    return user


CurrentUser = Annotated[User, Depends(current_user)]
